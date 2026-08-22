from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.profile import Profile
from app.schemas.profile import ProfileUpdate, ProfileResponse
from app.schemas.common import StandardResponse
from app.api.deps import get_current_user

router = APIRouter(prefix="/profiles", tags=["Profiles"])


@router.get("/me", response_model=StandardResponse[ProfileResponse])
async def get_my_profile(
    current_user: Profile = Depends(get_current_user),
):
    """Get authenticated profile."""
    return StandardResponse(data=ProfileResponse.model_validate(current_user))


@router.patch("/me", response_model=StandardResponse[ProfileResponse])
async def update_my_profile(
    payload: ProfileUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    """Update authenticated profile."""
    if payload.full_name is not None:
        current_user.full_name = payload.full_name
    if payload.avatar_url is not None:
        current_user.avatar_url = payload.avatar_url
    if payload.phone is not None:
        current_user.phone = payload.phone
    if payload.bio is not None:
        current_user.bio = payload.bio

    await db.flush()
    return StandardResponse(data=ProfileResponse.model_validate(current_user), message="Profile updated")
