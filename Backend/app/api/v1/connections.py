import uuid
from typing import List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.exceptions import NotFoundException, ForbiddenException, ConflictException
from app.models.profile import Profile
from app.models.provider import Provider
from app.models.provider_service import ProviderService
from app.models.request import Request
from app.models.connection import Connection
from app.models.enums import ConnectionStatus, RequestStatus
from app.schemas.connection import ConnectionCreate, ConnectionResponse
from app.schemas.provider import ProviderResponse
from app.schemas.profile import ProfileResponse
from app.schemas.common import StandardResponse
from app.api.deps import get_current_user
from app.services.trust_service import TrustService

router = APIRouter(prefix="/connections", tags=["Connections"])


@router.post("", response_model=StandardResponse[ConnectionResponse])
async def create_connection(
    payload: ConnectionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    """
    User connects with a matched provider ("CONNECT").
    Initiates a connection request.
    """
    # Check request ownership
    req_stmt = select(Request).where(Request.id == payload.request_id)
    req_obj = (await db.execute(req_stmt)).scalar_one_or_none()

    if not req_obj or req_obj.requester_id != current_user.id:
        raise ForbiddenException("Unauthorized to initiate connection for this request")

    # Check if connection already exists
    conn_stmt = select(Connection).where(
        Connection.request_id == payload.request_id,
        Connection.provider_id == payload.provider_id,
    )
    existing_conn = (await db.execute(conn_stmt)).scalar_one_or_none()
    if existing_conn:
        raise ConflictException("Connection already exists for this request and provider")

    now = datetime.now(timezone.utc)
    connection = Connection(
        request_id=payload.request_id,
        provider_id=payload.provider_id,
        requester_id=current_user.id,
        match_id=payload.match_id,
        status=ConnectionStatus.PENDING,
        created_at=now,
        updated_at=now,
    )
    db.add(connection)

    # Update request status
    req_obj.status = RequestStatus.CONNECTED
    req_obj.updated_at = now

    await db.flush()

    dto = await load_connection_dto(db, connection.id)
    return StandardResponse(data=dto, message="Connection request sent to provider")


@router.get("", response_model=StandardResponse[List[ConnectionResponse]])
async def list_connections(
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    """List connections where the user is requester or provider."""
    prov_stmt = select(Provider).where(Provider.user_id == current_user.id)
    user_provider = (await db.execute(prov_stmt)).scalar_one_or_none()
    user_provider_id = user_provider.id if user_provider else None

    stmt = (
        select(Connection)
        .where(
            (Connection.requester_id == current_user.id) | (Connection.provider_id == user_provider_id)
        )
        .order_by(Connection.created_at.desc())
        .options(
            selectinload(Connection.provider).selectinload(Provider.services).selectinload(ProviderService.service),
            selectinload(Connection.provider).selectinload(Provider.locations),
            selectinload(Connection.provider).selectinload(Provider.availabilities),
            selectinload(Connection.provider).selectinload(Provider.trust_score),
            selectinload(Connection.requester),
        )
    )

    res = await db.execute(stmt)
    connections = res.scalars().all()

    dtos = []
    for c in connections:
        p_dto = ProviderResponse.model_validate(c.provider) if c.provider else None
        r_dto = ProfileResponse.model_validate(c.requester) if c.requester else None
        dto = ConnectionResponse.model_validate(c)
        dto.provider = p_dto
        dto.requester = r_dto
        dtos.append(dto)

    return StandardResponse(data=dtos)


@router.get("/{connection_id}", response_model=StandardResponse[ConnectionResponse])
async def get_connection(
    connection_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    """Get connection details."""
    dto = await load_connection_dto(db, connection_id)

    # Authorization
    prov_stmt = select(Provider).where(Provider.user_id == current_user.id)
    user_provider = (await db.execute(prov_stmt)).scalar_one_or_none()
    user_provider_id = user_provider.id if user_provider else None

    if dto.requester_id != current_user.id and dto.provider_id != user_provider_id:
        raise ForbiddenException("Unauthorized to view this connection")

    return StandardResponse(data=dto)


@router.post("/{connection_id}/accept", response_model=StandardResponse[ConnectionResponse])
async def accept_connection(
    connection_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    """Provider accepts connection request."""
    conn = await get_connection_model(db, connection_id)

    prov_stmt = select(Provider).where(Provider.user_id == current_user.id)
    user_provider = (await db.execute(prov_stmt)).scalar_one_or_none()

    if not user_provider or conn.provider_id != user_provider.id:
        raise ForbiddenException("Only the designated provider can accept this connection")

    conn.status = ConnectionStatus.ACTIVE
    conn.connected_at = datetime.now(timezone.utc)
    conn.updated_at = datetime.now(timezone.utc)
    await db.flush()

    dto = await load_connection_dto(db, connection_id)
    return StandardResponse(data=dto, message="Connection accepted")


@router.post("/{connection_id}/decline", response_model=StandardResponse[ConnectionResponse])
async def decline_connection(
    connection_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    """Provider declines connection request."""
    conn = await get_connection_model(db, connection_id)

    prov_stmt = select(Provider).where(Provider.user_id == current_user.id)
    user_provider = (await db.execute(prov_stmt)).scalar_one_or_none()

    if not user_provider or conn.provider_id != user_provider.id:
        raise ForbiddenException("Only the designated provider can decline this connection")

    conn.status = ConnectionStatus.CANCELLED
    conn.cancelled_at = datetime.now(timezone.utc)
    conn.updated_at = datetime.now(timezone.utc)
    await db.flush()

    dto = await load_connection_dto(db, connection_id)
    return StandardResponse(data=dto, message="Connection declined")


@router.post("/{connection_id}/complete", response_model=StandardResponse[ConnectionResponse])
async def complete_connection(
    connection_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    """
    Confirms job completion by caller (requester or provider).
    Completion Gate: status flips to 'completed' only when both sides have confirmed.
    """
    conn = await get_connection_model(db, connection_id)

    prov_stmt = select(Provider).where(Provider.user_id == current_user.id)
    user_provider = (await db.execute(prov_stmt)).scalar_one_or_none()
    user_provider_id = user_provider.id if user_provider else None

    is_requester = conn.requester_id == current_user.id
    is_provider = conn.provider_id == user_provider_id

    if not (is_requester or is_provider):
        raise ForbiddenException("Not a participant in this connection")

    now = datetime.now(timezone.utc)
    if is_requester and conn.requester_confirmed_at is None:
        conn.requester_confirmed_at = now

    if is_provider and conn.provider_confirmed_at is None:
        conn.provider_confirmed_at = now

    # Check if both sides confirmed completion
    if conn.requester_confirmed_at is not None and conn.provider_confirmed_at is not None:
        conn.status = ConnectionStatus.COMPLETED
        conn.completed_at = now

        # Update provider completed jobs count
        prov_obj = (await db.execute(select(Provider).where(Provider.id == conn.provider_id))).scalar_one()
        prov_obj.completed_jobs += 1

        # Update request status to COMPLETED
        req_obj = (await db.execute(select(Request).where(Request.id == conn.request_id))).scalar_one_or_none()
        if req_obj:
            req_obj.status = RequestStatus.COMPLETED

        await db.flush()
        # Recalculate provider trust score
        await TrustService.recalculate_provider_trust(db, conn.provider_id)

    conn.updated_at = now
    await db.flush()

    dto = await load_connection_dto(db, connection_id)
    msg = "Connection completed!" if conn.status == ConnectionStatus.COMPLETED else "Completion confirmed. Waiting for other party."
    return StandardResponse(data=dto, message=msg)


async def get_connection_model(db: AsyncSession, connection_id: uuid.UUID) -> Connection:
    stmt = select(Connection).where(Connection.id == connection_id)
    res = await db.execute(stmt)
    conn = res.scalar_one_or_none()
    if not conn:
        raise NotFoundException("Connection not found")
    return conn


async def load_connection_dto(db: AsyncSession, connection_id: uuid.UUID) -> ConnectionResponse:
    stmt = (
        select(Connection)
        .where(Connection.id == connection_id)
        .options(
            selectinload(Connection.provider).selectinload(Provider.services).selectinload(ProviderService.service),
            selectinload(Connection.provider).selectinload(Provider.locations),
            selectinload(Connection.provider).selectinload(Provider.availabilities),
            selectinload(Connection.provider).selectinload(Provider.trust_score),
            selectinload(Connection.requester),
        )
    )
    res = await db.execute(stmt)
    conn = res.scalar_one_or_none()
    if not conn:
        raise NotFoundException("Connection not found")

    p_dto = ProviderResponse.model_validate(conn.provider) if conn.provider else None
    r_dto = ProfileResponse.model_validate(conn.requester) if conn.requester else None
    dto = ConnectionResponse.model_validate(conn)
    dto.provider = p_dto
    dto.requester = r_dto
    return dto
