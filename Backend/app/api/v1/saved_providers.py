import uuid
from typing import List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.exceptions import NotFoundException, ConflictException
from app.models.profile import Profile
from app.models.provider import Provider
from app.models.saved_provider import SavedProvider
from app.schemas.provider import ProviderResponse
from app.schemas.common import StandardResponse
from app.api.deps import get_current_user

router = APIRouter(tags=["Saved Providers"])


@router.post("/providers/{provider_id}/save", response_model=StandardResponse[dict], status_code=status.HTTP_201_CREATED)
async def save_provider(
    provider_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    """Bookmark a provider."""
    # Check provider existence
    prov_stmt = select(Provider).where(Provider.id == provider_id)
    if not (await db.execute(prov_stmt)).scalar_one_or_none():
        raise NotFoundException("Provider not found")

    sp_stmt = select(SavedProvider).where(
        SavedProvider.user_id == current_user.id,
        SavedProvider.provider_id == provider_id,
    )
    if (await db.execute(sp_stmt)).scalar_one_or_none():
        raise ConflictException("Provider is already saved")

    sp = SavedProvider(
        user_id=current_user.id,
        provider_id=provider_id,
        created_at=datetime.now(timezone.utc),
    )
    db.add(sp)
    await db.flush()

    return StandardResponse(data={"saved": True}, message="Provider saved")


@router.delete("/providers/{provider_id}/save", response_model=StandardResponse[dict])
async def remove_saved_provider(
    provider_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    """Remove a provider from saved bookmarks."""
    sp_stmt = select(SavedProvider).where(
        SavedProvider.user_id == current_user.id,
        SavedProvider.provider_id == provider_id,
    )
    sp = (await db.execute(sp_stmt)).scalar_one_or_none()
    if not sp:
        raise NotFoundException("Saved provider bookmark not found")

    await db.delete(sp)
    await db.flush()

    return StandardResponse(data={"saved": False}, message="Provider bookmark removed")


@router.get("/saved-providers", response_model=StandardResponse[List[ProviderResponse]])
async def list_saved_providers(
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    """List authenticated user's saved providers."""
    stmt = (
        select(SavedProvider)
        .where(SavedProvider.user_id == current_user.id)
        .options(
            selectinload(SavedProvider.provider).selectinload(Provider.services),
            selectinload(SavedProvider.provider).selectinload(Provider.locations),
            selectinload(SavedProvider.provider).selectinload(Provider.trust_score),
        )
    )
    res = await db.execute(stmt)
    saved_list = res.scalars().all()

    dtos = []
    for sp in saved_list:
        if sp.provider:
            dto = ProviderResponse.model_validate(sp.provider)
            if sp.provider.trust_score:
                dto.trust_score = float(sp.provider.trust_score.trust_score)
            dtos.append(dto)

    return StandardResponse(data=dtos)
