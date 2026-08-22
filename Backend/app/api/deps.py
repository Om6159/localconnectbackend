import uuid
from typing import AsyncGenerator
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import decode_access_token
from app.core.exceptions import UnauthorizedException, ForbiddenException
from app.models.profile import Profile
from app.models.provider import Provider

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme),
) -> Profile:
    """Dependency to retrieve the currently authenticated user profile from JWT token."""
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise UnauthorizedException("Invalid or expired authentication token")

    try:
        user_id = uuid.UUID(str(payload["sub"]))
    except (ValueError, TypeError):
        raise UnauthorizedException("Invalid user ID in token")

    stmt = select(Profile).where(Profile.id == user_id)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()

    if not user:
        raise UnauthorizedException("User profile not found")

    return user


async def get_current_provider(
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
) -> Provider:
    """Dependency to retrieve the current user's provider profile."""
    stmt = select(Provider).where(Provider.user_id == current_user.id)
    res = await db.execute(stmt)
    provider = res.scalar_one_or_none()

    if not provider:
        raise ForbiddenException("User is not registered as a provider")

    return provider
