import uuid
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.exceptions import NotFoundException, ConflictException, ForbiddenException
from app.models.profile import Profile
from app.models.provider import Provider
from app.models.provider_service import ProviderService
from app.models.availability import ProviderAvailability
from app.models.location import Location
from app.schemas.provider import (
    ProviderCreate,
    ProviderUpdate,
    ProviderResponse,
    ProviderServiceCreate,
    ProviderServiceResponse,
)
from app.schemas.availability import AvailabilityCreate, AvailabilityResponse
from app.schemas.common import StandardResponse
from app.api.deps import get_current_user
from app.services.trust_service import TrustService

router = APIRouter(prefix="/providers", tags=["Providers"])


@router.post("", response_model=StandardResponse[ProviderResponse], status_code=status.HTTP_201_CREATED)
async def create_provider(
    payload: ProviderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    """Create a provider profile for the authenticated user."""
    # Check if provider profile already exists
    stmt = select(Provider).where(Provider.user_id == current_user.id)
    res = await db.execute(stmt)
    if res.scalar_one_or_none():
        raise ConflictException("User already has a provider profile")

    provider = Provider(
        user_id=current_user.id,
        display_name=payload.display_name,
        bio=payload.bio,
        experience_years=payload.experience_years,
        service_radius_km=payload.service_radius_km,
    )
    db.add(provider)
    await db.flush()

    # Add services if provided
    if payload.services:
        for ps in payload.services:
            p_service = ProviderService(
                provider_id=provider.id,
                service_id=ps.service_id,
                price_from=ps.price_from,
                price_to=ps.price_to,
                experience_years=ps.experience_years,
                is_primary=ps.is_primary,
            )
            db.add(p_service)

    # Add location if provided
    if payload.location:
        loc = Location(
            provider_id=provider.id,
            label=payload.location.get("label", "Primary"),
            locality=payload.location.get("locality"),
            city=payload.location.get("city", "Mumbai"),
            state=payload.location.get("state"),
            pincode=payload.location.get("pincode"),
            latitude=float(payload.location.get("latitude", 19.0760)),
            longitude=float(payload.location.get("longitude", 72.8777)),
            is_primary=True,
        )
        db.add(loc)

    await db.flush()
    await TrustService.recalculate_provider_trust(db, provider.id)

    # Reload full provider
    full_prov = await get_provider_by_id_internal(db, provider.id)
    return StandardResponse(data=full_prov, message="Provider profile created")


@router.get("", response_model=StandardResponse[List[ProviderResponse]])
async def list_providers(
    db: AsyncSession = Depends(get_db),
):
    """List all active provider profiles."""
    stmt = (
        select(Provider)
        .where(Provider.is_active == True)
        .options(
            selectinload(Provider.services).selectinload(ProviderService.service),
            selectinload(Provider.locations),
            selectinload(Provider.availabilities),
            selectinload(Provider.trust_score),
        )
    )
    res = await db.execute(stmt)
    providers = res.scalars().all()

    dtos = []
    for p in providers:
        dto = ProviderResponse.model_validate(p)
        if p.trust_score:
            dto.trust_score = float(p.trust_score.trust_score)
        dtos.append(dto)

    return StandardResponse(data=dtos)


@router.get("/{provider_id}", response_model=StandardResponse[ProviderResponse])
async def get_provider(
    provider_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get detailed provider profile by ID."""
    dto = await get_provider_by_id_internal(db, provider_id)
    return StandardResponse(data=dto)


@router.patch("/{provider_id}", response_model=StandardResponse[ProviderResponse])
async def update_provider(
    provider_id: uuid.UUID,
    payload: ProviderUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    """Update provider profile (owner only)."""
    stmt = select(Provider).where(Provider.id == provider_id)
    res = await db.execute(stmt)
    provider = res.scalar_one_or_none()

    if not provider:
        raise NotFoundException("Provider not found")
    if provider.user_id != current_user.id:
        raise ForbiddenException("Cannot edit another provider's profile")

    if payload.display_name is not None:
        provider.display_name = payload.display_name
    if payload.bio is not None:
        provider.bio = payload.bio
    if payload.experience_years is not None:
        provider.experience_years = payload.experience_years
    if payload.service_radius_km is not None:
        provider.service_radius_km = payload.service_radius_km
    if payload.is_active is not None:
        provider.is_active = payload.is_active

    await db.flush()
    await TrustService.recalculate_provider_trust(db, provider.id)

    full_prov = await get_provider_by_id_internal(db, provider.id)
    return StandardResponse(data=full_prov, message="Provider profile updated")


@router.get("/{provider_id}/services", response_model=StandardResponse[List[ProviderServiceResponse]])
async def get_provider_services(
    provider_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get services offered by provider."""
    stmt = (
        select(ProviderService)
        .where(ProviderService.provider_id == provider_id)
        .options(selectinload(ProviderService.service))
    )
    res = await db.execute(stmt)
    services = res.scalars().all()
    dtos = [ProviderServiceResponse.model_validate(s) for s in services]
    return StandardResponse(data=dtos)


@router.post("/{provider_id}/services", response_model=StandardResponse[ProviderServiceResponse])
async def add_provider_service(
    provider_id: uuid.UUID,
    payload: ProviderServiceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    """Add a new service to provider's profile."""
    stmt = select(Provider).where(Provider.id == provider_id)
    res = await db.execute(stmt)
    provider = res.scalar_one_or_none()

    if not provider or provider.user_id != current_user.id:
        raise ForbiddenException("Unauthorized to modify provider services")

    ps = ProviderService(
        provider_id=provider_id,
        service_id=payload.service_id,
        price_from=payload.price_from,
        price_to=payload.price_to,
        experience_years=payload.experience_years,
        is_primary=payload.is_primary,
    )
    db.add(ps)
    await db.flush()
    await TrustService.recalculate_provider_trust(db, provider_id)

    # Reload
    loaded_ps = (
        await db.execute(
            select(ProviderService)
            .where(ProviderService.provider_id == provider_id, ProviderService.service_id == payload.service_id)
            .options(selectinload(ProviderService.service))
        )
    ).scalar_one()

    return StandardResponse(data=ProviderServiceResponse.model_validate(loaded_ps))


@router.get("/{provider_id}/availability", response_model=StandardResponse[List[AvailabilityResponse]])
async def get_provider_availability(
    provider_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get provider weekly availability."""
    stmt = select(ProviderAvailability).where(ProviderAvailability.provider_id == provider_id)
    res = await db.execute(stmt)
    avails = res.scalars().all()
    dtos = [AvailabilityResponse.model_validate(a) for a in avails]
    return StandardResponse(data=dtos)


@router.patch("/{provider_id}/availability", response_model=StandardResponse[List[AvailabilityResponse]])
async def update_provider_availability(
    provider_id: uuid.UUID,
    payload: List[AvailabilityCreate],
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    """Update provider weekly availability slots."""
    stmt = select(Provider).where(Provider.id == provider_id)
    res = await db.execute(stmt)
    provider = res.scalar_one_or_none()

    if not provider or provider.user_id != current_user.id:
        raise ForbiddenException("Unauthorized to modify provider availability")

    # Clear existing availability slots
    clear_stmt = select(ProviderAvailability).where(ProviderAvailability.provider_id == provider_id)
    existing_avails = (await db.execute(clear_stmt)).scalars().all()
    for ex in existing_avails:
        await db.delete(ex)

    # Add new slots
    new_avails = []
    for slot in payload:
        pa = ProviderAvailability(
            provider_id=provider_id,
            day_of_week=slot.day_of_week,
            start_time=slot.start_time,
            end_time=slot.end_time,
            is_available=slot.is_available,
        )
        db.add(pa)
        new_avails.append(pa)

    await db.flush()
    await TrustService.recalculate_provider_trust(db, provider_id)

    dtos = [AvailabilityResponse.model_validate(a) for a in new_avails]
    return StandardResponse(data=dtos, message="Availability updated")


async def get_provider_by_id_internal(db: AsyncSession, provider_id: uuid.UUID) -> ProviderResponse:
    stmt = (
        select(Provider)
        .where(Provider.id == provider_id)
        .options(
            selectinload(Provider.services).selectinload(ProviderService.service),
            selectinload(Provider.locations),
            selectinload(Provider.availabilities),
            selectinload(Provider.trust_score),
        )
    )
    res = await db.execute(stmt)
    provider = res.scalar_one_or_none()
    if not provider:
        raise NotFoundException("Provider not found")

    dto = ProviderResponse.model_validate(provider)
    if provider.trust_score:
        dto.trust_score = float(provider.trust_score.trust_score)
    return dto
