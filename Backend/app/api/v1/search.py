import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.provider import Provider
from app.models.provider_service import ProviderService
from app.models.location import Location
from app.schemas.provider import ProviderResponse
from app.schemas.common import StandardResponse
from app.utils.geo import haversine_distance_km

router = APIRouter(prefix="/search", tags=["Search & Discover"])


@router.get("/providers", response_model=StandardResponse[List[ProviderResponse]])
async def search_providers(
    category_id: Optional[uuid.UUID] = Query(None),
    service_id: Optional[uuid.UUID] = Query(None),
    latitude: Optional[float] = Query(None),
    longitude: Optional[float] = Query(None),
    radius_km: float = Query(10.0),
    max_budget: Optional[float] = Query(None),
    min_rating: Optional[float] = Query(None),
    min_experience: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Search active providers using PostGIS / spatial coordinates and optional filters.
    """
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

    if min_rating:
        stmt = stmt.where(Provider.average_rating >= min_rating)
    if min_experience:
        stmt = stmt.where(Provider.experience_years >= min_experience)

    res = await db.execute(stmt)
    providers = res.scalars().all()

    filtered_dtos = []
    for p in providers:
        # Category / Service filter
        if service_id:
            if not any(ps.service_id == service_id for ps in p.services):
                continue
        elif category_id:
            if not any(ps.service and ps.service.category_id == category_id for ps in p.services):
                continue

        # Budget filter
        if max_budget is not None:
            prices = [float(ps.price_from) for ps in p.services if ps.price_from is not None]
            if prices and min(prices) > max_budget:
                continue

        # Distance filter
        dist = None
        if latitude is not None and longitude is not None:
            prim_loc = next((loc for loc in p.locations if loc.is_primary), None)
            if not prim_loc and p.locations:
                prim_loc = p.locations[0]

            if prim_loc:
                dist = haversine_distance_km(latitude, longitude, prim_loc.latitude, prim_loc.longitude)
                if dist > radius_km:
                    continue

        dto = ProviderResponse.model_validate(p)
        if p.trust_score:
            dto.trust_score = float(p.trust_score.trust_score)
        filtered_dtos.append(dto)

    # Sort by average rating and trust
    filtered_dtos.sort(key=lambda x: (x.trust_score or 0.0, x.average_rating), reverse=True)

    return StandardResponse(data=filtered_dtos)
