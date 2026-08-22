import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.exceptions import NotFoundException
from app.models.trust import ProviderTrustScore
from app.schemas.trust import TrustScoreBreakdown
from app.schemas.common import StandardResponse
from app.services.trust_service import TrustService

router = APIRouter(tags=["Trust System"])


@router.get("/providers/{provider_id}/trust", response_model=StandardResponse[TrustScoreBreakdown])
async def get_provider_trust(
    provider_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve detailed Trust Score breakdown for a provider."""
    stmt = select(ProviderTrustScore).where(ProviderTrustScore.provider_id == provider_id)
    res = await db.execute(stmt)
    trust_rec = res.scalar_one_or_none()

    if not trust_rec:
        # Recalculate on the fly
        trust_dto = await TrustService.recalculate_provider_trust(db, provider_id)
        return StandardResponse(data=trust_dto)

    dto = TrustScoreBreakdown.model_validate(trust_rec)
    return StandardResponse(data=dto)


@router.post("/providers/{provider_id}/recalculate-trust", response_model=StandardResponse[TrustScoreBreakdown])
async def recalculate_provider_trust_endpoint(
    provider_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Trigger recalculation of Canonical Trust Score for a provider."""
    trust_dto = await TrustService.recalculate_provider_trust(db, provider_id)
    return StandardResponse(data=trust_dto, message="Trust score recalculated")
