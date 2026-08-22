import uuid
from typing import List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.exceptions import NotFoundException, ForbiddenException
from app.models.profile import Profile
from app.models.provider import Provider
from app.models.request import Request
from app.models.match import RequestMatch
from app.schemas.match import MatchResponse, MatchRespondRequest
from app.schemas.provider import ProviderResponse
from app.schemas.common import StandardResponse
from app.api.deps import get_current_user
from app.services.matching_service import MatchingService

router = APIRouter(tags=["Matches"])


@router.post("/requests/{request_id}/match", response_model=StandardResponse[List[MatchResponse]])
async def run_matching(
    request_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    """
    Run deterministic matching engine for a requirement ("MATCH").
    Filters active nearby providers, calculates score components, and returns ranked matches with explanations.
    """
    # Authorization check
    stmt = select(Request).where(Request.id == request_id)
    res = await db.execute(stmt)
    req_obj = res.scalar_one_or_none()

    if not req_obj:
        raise NotFoundException("Request not found")
    if req_obj.requester_id != current_user.id:
        raise ForbiddenException("Unauthorized to run matching for this request")

    matches = await MatchingService.match_request(db, request_id)
    return StandardResponse(data=matches, message=f"Found {len(matches)} matching providers")


@router.get("/requests/{request_id}/matches", response_model=StandardResponse[List[MatchResponse]])
async def get_request_matches(
    request_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    """Retrieve saved match results for a request."""
    stmt = (
        select(RequestMatch)
        .where(RequestMatch.request_id == request_id)
        .order_by(RequestMatch.total_match_score.desc())
        .options(
            selectinload(RequestMatch.provider).selectinload(Provider.services),
            selectinload(RequestMatch.provider).selectinload(Provider.locations),
            selectinload(RequestMatch.provider).selectinload(Provider.trust_score),
        )
    )
    res = await db.execute(stmt)
    matches_db = res.scalars().all()

    dtos = []
    for m in matches_db:
        provider_dto = ProviderResponse.model_validate(m.provider)
        if m.provider.trust_score:
            provider_dto.trust_score = float(m.provider.trust_score.trust_score)

        dto = MatchResponse(
            id=m.id,
            request_id=m.request_id,
            provider_id=m.provider_id,
            distance_km=float(m.distance_km) if m.distance_km is not None else None,
            service_score=float(m.service_score),
            availability_score=float(m.availability_score),
            price_score=float(m.price_score),
            rating_score=float(m.rating_score),
            trust_score=float(m.trust_score),
            total_match_score=float(m.total_match_score),
            status=m.status,
            provider_response=m.provider_response,
            provider_responded_at=m.provider_responded_at,
            created_at=m.created_at,
            updated_at=m.updated_at,
            provider=provider_dto,
            match_explanations=[
                "✓ Skill relevance match",
                f"✓ Total match score {int(m.total_match_score)}%",
            ],
        )
        dtos.append(dto)

    return StandardResponse(data=dtos)


@router.post("/matches/{match_id}/respond", response_model=StandardResponse[MatchResponse])
async def respond_to_match(
    match_id: uuid.UUID,
    payload: MatchRespondRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    """Provider responds to a match (interested, declined, etc.)."""
    stmt = (
        select(RequestMatch)
        .where(RequestMatch.id == match_id)
        .options(
            selectinload(RequestMatch.provider),
            selectinload(RequestMatch.request)
        )
    )
    res = await db.execute(stmt)
    match_obj = res.scalar_one_or_none()

    if not match_obj:
        raise NotFoundException("Match not found")
    if match_obj.provider.user_id != current_user.id:
        raise ForbiddenException("Only the matched provider can respond")

    match_obj.status = payload.status
    match_obj.provider_response = payload.response_text
    match_obj.provider_responded_at = datetime.now(timezone.utc)
    match_obj.updated_at = datetime.now(timezone.utc)

    # Recalculate response rate for provider
    provider_id = match_obj.provider_id
    total_assigned_stmt = select(RequestMatch).where(RequestMatch.provider_id == provider_id)
    total_assigned = len((await db.execute(total_assigned_stmt)).scalars().all())

    total_responded_stmt = select(RequestMatch).where(
        RequestMatch.provider_id == provider_id, RequestMatch.provider_response != None
    )
    total_responded = len((await db.execute(total_responded_stmt)).scalars().all())

    if total_assigned > 0:
        match_obj.provider.response_rate = round((total_responded / total_assigned) * 100.0, 2)

    await db.flush()

    provider_dto = ProviderResponse.model_validate(match_obj.provider)
    dto = MatchResponse(
        id=match_obj.id,
        request_id=match_obj.request_id,
        provider_id=match_obj.provider_id,
        distance_km=float(match_obj.distance_km) if match_obj.distance_km is not None else None,
        service_score=float(match_obj.service_score),
        availability_score=float(match_obj.availability_score),
        price_score=float(match_obj.price_score),
        rating_score=float(match_obj.rating_score),
        trust_score=float(match_obj.trust_score),
        total_match_score=float(match_obj.total_match_score),
        status=match_obj.status,
        provider_response=match_obj.provider_response,
        provider_responded_at=match_obj.provider_responded_at,
        created_at=match_obj.created_at,
        updated_at=match_obj.updated_at,
        provider=provider_dto,
    )
    return StandardResponse(data=dto, message="Match response updated")
