from datetime import timedelta
from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_password_hash, verify_password, create_access_token
from app.core.config import settings
from app.core.exceptions import ConflictException, UnauthorizedException
from app.models.profile import Profile
from app.schemas.auth import RegisterRequest, TokenResponse
from app.schemas.profile import ProfileResponse
from app.schemas.common import StandardResponse
from app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=StandardResponse[ProfileResponse], status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """Register a new user profile with email and password."""
    stmt = select(Profile).where(Profile.email == payload.email)
    res = await db.execute(stmt)
    existing = res.scalar_one_or_none()
    if existing:
        raise ConflictException("Email already registered")

    user = Profile(
        email=payload.email,
        hashed_password=get_password_hash(payload.password),
        full_name=payload.full_name,
        phone=payload.phone,
        bio=payload.bio,
    )
    db.add(user)
    await db.flush()

    profile_dto = ProfileResponse.model_validate(user)
    return StandardResponse(data=profile_dto, message="User registered successfully")


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """Authenticate user and return a JWT access token."""
    stmt = select(Profile).where(Profile.email == form_data.username)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise UnauthorizedException("Incorrect email or password")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(
        subject=str(user.id), expires_delta=access_token_expires
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.get("/me", response_model=StandardResponse[ProfileResponse])
async def get_me(
    current_user: Profile = Depends(get_current_user),
):
    """Retrieve the authenticated user's profile."""
    return StandardResponse(data=ProfileResponse.model_validate(current_user))
