import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.core.exceptions import NotFoundException, ForbiddenException, BadRequestException, ConflictException
from app.models.profile import Profile
from app.models.provider import Provider
from app.models.connection import Connection
from app.models.recommendation import ProviderRecommendation
from app.models.enums import ConnectionStatus
from app.schemas.recommendation import CommunityRecommendationCreate, CommunityRecommendationResponse
from app.schemas.common import StandardResponse
from app.api.deps import get_current_user
from app.services.trust_service import TrustService

router = APIRouter(tags=["Community Recommendations"])


@router.post("/providers/{provider_id}/recommend", response_model=StandardResponse[CommunityRecommendationResponse], status_code=status.HTTP_201_CREATED)
async def recommend_provider(
    provider_id: uuid.UUID,
    payload: CommunityRecommendationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    """
    Vouch for a provider ("Community Recommendation").
    Requires a valid completed connection between recommender and provider.
    """
    # 1. Prevent self recommendation
    prov_stmt = select(Provider).where(Provider.id == provider_id)
    provider_obj = (await db.execute(prov_stmt)).scalar_one_or_none()
    if not provider_obj:
        raise NotFoundException("Provider not found")
    if provider_obj.user_id == current_user.id:
        raise BadRequestException("Providers cannot recommend their own profile")

    # 2. Check completed connection
    conn_stmt = select(Connection).where(
        Connection.id == payload.connection_id,
        Connection.provider_id == provider_id,
    )
    conn = (await db.execute(conn_stmt)).scalar_one_or_none()
    if not conn:
        raise BadRequestException("Invalid connection reference for this provider")
    if conn.status != ConnectionStatus.COMPLETED:
        raise BadRequestException("Recommendations require a completed connection")

    if conn.requester_id != current_user.id:
        raise ForbiddenException("Only participants in the completed connection can vouch for this provider")

    # 3. Check duplicate active recommendation
    rec_stmt = select(ProviderRecommendation).where(
        ProviderRecommendation.recommender_id == current_user.id,
        ProviderRecommendation.provider_id == provider_id,
    )
    existing_rec = (await db.execute(rec_stmt)).scalar_one_or_none()
    if existing_rec:
        if existing_rec.is_active:
            raise ConflictException("You have already recommended this provider")
        else:
            existing_rec.is_active = True
            await db.flush()
            rec_obj = existing_rec
    else:
        rec_obj = ProviderRecommendation(
            recommender_id=current_user.id,
            provider_id=provider_id,
            connection_id=payload.connection_id,
            is_active=True,
            created_at=datetime.now(timezone.utc),
        )
        db.add(rec_obj)
        await db.flush()

    # 4. Update provider recommendation count & trust score
    cnt_stmt = select(func.count(ProviderRecommendation.id)).where(
        ProviderRecommendation.provider_id == provider_id,
        ProviderRecommendation.is_active == True,
    )
    active_cnt = (await db.execute(cnt_stmt)).scalar() or 0
    provider_obj.recommendation_count = active_cnt
    await db.flush()

    await TrustService.recalculate_provider_trust(db, provider_id)

    dto = CommunityRecommendationResponse.model_validate(rec_obj)
    return StandardResponse(data=dto, message="Recommendation added successfully")


@router.delete("/providers/{provider_id}/recommend", response_model=StandardResponse[dict])
async def revoke_recommendation(
    provider_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    """Revoke a previously submitted community recommendation."""
    rec_stmt = select(ProviderRecommendation).where(
        ProviderRecommendation.recommender_id == current_user.id,
        ProviderRecommendation.provider_id == provider_id,
        ProviderRecommendation.is_active == True,
    )
    rec_obj = (await db.execute(rec_stmt)).scalar_one_or_none()

    if not rec_obj:
        raise NotFoundException("Active recommendation not found")

    rec_obj.is_active = False
    await db.flush()

    # Update count
    cnt_stmt = select(func.count(ProviderRecommendation.id)).where(
        ProviderRecommendation.provider_id == provider_id,
        ProviderRecommendation.is_active == True,
    )
    active_cnt = (await db.execute(cnt_stmt)).scalar() or 0

    prov_stmt = select(Provider).where(Provider.id == provider_id)
    provider_obj = (await db.execute(prov_stmt)).scalar_one()
    provider_obj.recommendation_count = active_cnt
    await db.flush()

    await TrustService.recalculate_provider_trust(db, provider_id)

    return StandardResponse(data={"success": True}, message="Recommendation revoked")
