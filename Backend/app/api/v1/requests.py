import uuid
from typing import List
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.exceptions import NotFoundException, ForbiddenException
from app.models.profile import Profile
from app.models.request import Request
from app.models.enums import RequestStatus
from app.schemas.request import RequestCreate, RequestUpdate, RequestResponse
from app.schemas.common import StandardResponse
from app.api.deps import get_current_user
from app.services.ai_service import AIService

router = APIRouter(prefix="/requests", tags=["Requests"])


@router.post("", response_model=StandardResponse[RequestResponse], status_code=status.HTTP_201_CREATED)
async def create_request(
    payload: RequestCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    """
    Submit a service requirement in natural language ("NEED").
    Runs AI parsing service to produce structured JSON requirement and creates request.
    """
    ai_result = await AIService.parse_requirement(payload.raw_description)

    # Use AI parsed budget / radius if payload left them blank
    budget_max = payload.budget_max if payload.budget_max is not None else ai_result.budget_max
    budget_min = payload.budget_min if payload.budget_min is not None else ai_result.budget_min
    radius_km = payload.radius_km if payload.radius_km is not None else (ai_result.radius_km or 5.0)

    # Set default location if lat/lng missing (Mumbai central default for hackathon demo if unspecified)
    latitude = payload.latitude if payload.latitude is not None else 19.0760
    longitude = payload.longitude if payload.longitude is not None else 72.8777

    req_obj = Request(
        requester_id=current_user.id,
        raw_description=payload.raw_description,
        ai_parsed_requirement=ai_result.model_dump(),
        ai_confidence=ai_result.confidence,
        category_id=payload.category_id,
        service_id=payload.service_id,
        budget_min=budget_min,
        budget_max=budget_max,
        radius_km=radius_km,
        latitude=latitude,
        longitude=longitude,
        status=RequestStatus.OPEN,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )
    db.add(req_obj)
    await db.flush()

    dto = RequestResponse.model_validate(req_obj)
    return StandardResponse(data=dto, message="Requirement created and parsed")


@router.get("", response_model=StandardResponse[List[RequestResponse]])
async def list_user_requests(
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    """List all requests created by the authenticated user."""
    stmt = select(Request).where(Request.requester_id == current_user.id).order_by(Request.created_at.desc())
    res = await db.execute(stmt)
    requests = res.scalars().all()
    dtos = [RequestResponse.model_validate(r) for r in requests]
    return StandardResponse(data=dtos)


@router.get("/{request_id}", response_model=StandardResponse[RequestResponse])
async def get_request(
    request_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    """Get detailed request information."""
    stmt = select(Request).where(Request.id == request_id)
    res = await db.execute(stmt)
    req_obj = res.scalar_one_or_none()

    if not req_obj:
        raise NotFoundException("Request not found")
    if req_obj.requester_id != current_user.id:
        raise ForbiddenException("Unauthorized to view this request")

    return StandardResponse(data=RequestResponse.model_validate(req_obj))


@router.patch("/{request_id}", response_model=StandardResponse[RequestResponse])
async def update_request(
    request_id: uuid.UUID,
    payload: RequestUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    """Update request fields."""
    stmt = select(Request).where(Request.id == request_id)
    res = await db.execute(stmt)
    req_obj = res.scalar_one_or_none()

    if not req_obj or req_obj.requester_id != current_user.id:
        raise ForbiddenException("Unauthorized to modify this request")

    if payload.raw_description is not None:
        req_obj.raw_description = payload.raw_description
    if payload.budget_min is not None:
        req_obj.budget_min = payload.budget_min
    if payload.budget_max is not None:
        req_obj.budget_max = payload.budget_max
    if payload.radius_km is not None:
        req_obj.radius_km = payload.radius_km
    if payload.status is not None:
        req_obj.status = payload.status

    req_obj.updated_at = datetime.now(timezone.utc)
    await db.flush()

    return StandardResponse(data=RequestResponse.model_validate(req_obj), message="Request updated")


@router.post("/{request_id}/cancel", response_model=StandardResponse[RequestResponse])
async def cancel_request(
    request_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    """Cancel an active request."""
    stmt = select(Request).where(Request.id == request_id)
    res = await db.execute(stmt)
    req_obj = res.scalar_one_or_none()

    if not req_obj or req_obj.requester_id != current_user.id:
        raise ForbiddenException("Unauthorized to cancel this request")

    req_obj.status = RequestStatus.CANCELLED
    req_obj.updated_at = datetime.now(timezone.utc)
    await db.flush()

    return StandardResponse(data=RequestResponse.model_validate(req_obj), message="Request cancelled")
