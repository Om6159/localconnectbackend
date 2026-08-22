import uuid
from datetime import datetime, timezone
from typing import List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.request import Request
from app.models.provider import Provider
from app.models.match import RequestMatch
from app.models.enums import RequestStatus, MatchStatus
from app.services.trust_service import TrustService
from app.schemas.match import MatchResponse
from app.schemas.provider import ProviderResponse
from app.utils.geo import haversine_distance_km


class MatchingService:
    @staticmethod
    async def match_request(
        db: AsyncSession, request_id: uuid.UUID
    ) -> List[MatchResponse]:
        """
        Executes the deterministic matching engine for a given service request.
        Calculates feature scores (Skill 30%, Distance 20%, Budget 15%, Availability 15%, Trust 10%, Rating 10%),
        ranks candidate providers, generates match explanations, and persists matches in request_matches.
        """
        # Fetch request
        req_stmt = (
            select(Request)
            .where(Request.id == request_id)
            .options(selectinload(Request.category), selectinload(Request.service))
        )
        req_res = await db.execute(req_stmt)
        request_obj = req_res.scalar_one_or_none()
        if not request_obj:
            raise ValueError("Request not found")

        # Fetch active providers with loaded relationships
        prov_stmt = (
            select(Provider)
            .where(Provider.is_active == True)
            .options(
                selectinload(Provider.services),
                selectinload(Provider.locations),
                selectinload(Provider.availabilities),
                selectinload(Provider.trust_score),
            )
        )
        providers_res = await db.execute(prov_stmt)
        candidate_providers = providers_res.scalars().all()

        matches: List[Tuple[RequestMatch, Provider, List[str]]] = []

        req_lat = request_obj.latitude
        req_lng = request_obj.longitude
        req_radius = float(request_obj.radius_km or 5.0)
        req_budget = float(request_obj.budget_max) if request_obj.budget_max else None

        parsed_req = request_obj.ai_parsed_requirement or {}
        req_avail_days = parsed_req.get("availability", [])

        for provider in candidate_providers:
            # Calculate distance
            distance_km = None
            primary_loc = next((loc for loc in provider.locations if loc.is_primary), None)
            if not primary_loc and provider.locations:
                primary_loc = provider.locations[0]

            if primary_loc and req_lat is not None and req_lng is not None:
                distance_km = haversine_distance_km(
                    req_lat, req_lng, primary_loc.latitude, primary_loc.longitude
                )

            # Skip if provider exceeds service radius or request radius
            effective_max_radius = max(req_radius, float(provider.service_radius_km or 5.0))
            if distance_km is not None and distance_km > effective_max_radius * 1.5:
                continue

            # 1. Skill Relevance Score (30%)
            service_score = 50.0  # default partial
            matching_service_name = None
            for ps in provider.services:
                if request_obj.service_id and ps.service_id == request_obj.service_id:
                    service_score = 100.0
                    matching_service_name = ps.service.name if ps.service else "matching service"
                    break
                elif request_obj.category_id and ps.service and ps.service.category_id == request_obj.category_id:
                    service_score = 80.0
                    matching_service_name = ps.service.name if ps.service else "matching category"

            if matching_service_name is None and provider.services:
                matching_service_name = provider.services[0].service.name if provider.services[0].service else "local service"

            # 2. Distance Score (20%)
            if distance_km is not None:
                dist_score_norm = max(0.0, 1.0 - (distance_km / req_radius))
                distance_score = round(dist_score_norm * 100.0, 2)
            else:
                distance_score = 50.0  # default neutral if coordinates missing

            # 3. Budget Fit Score (15%)
            price_score = 30.0  # unknown default
            min_provider_price = None
            for ps in provider.services:
                if ps.price_from is not None:
                    if min_provider_price is None or float(ps.price_from) < min_provider_price:
                        min_provider_price = float(ps.price_from)

            if req_budget is not None and min_provider_price is not None:
                if min_provider_price <= req_budget:
                    price_score = 100.0
                elif min_provider_price <= 1.10 * req_budget:
                    price_score = 70.0
                elif min_provider_price <= 1.25 * req_budget:
                    price_score = 40.0
                else:
                    price_score = 0.0

            # 4. Availability Score (15%)
            availability_score = 30.0  # unknown default
            if req_avail_days and provider.availabilities:
                avail_days_map = {0: "Monday", 1: "Tuesday", 2: "Wednesday", 3: "Thursday", 4: "Friday", 5: "Saturday", 6: "Sunday"}
                provider_active_days = set()
                for av in provider.availabilities:
                    if av.is_available:
                        day_name = avail_days_map.get(av.day_of_week)
                        if day_name:
                            provider_active_days.add(day_name)

                overlap = set(req_avail_days).intersection(provider_active_days)
                if len(overlap) == len(req_avail_days):
                    availability_score = 100.0
                elif len(overlap) > 0:
                    availability_score = 50.0
                else:
                    availability_score = 0.0

            # 5. Trust Score (10%)
            if provider.trust_score:
                t_score_val = float(provider.trust_score.trust_score)
            else:
                # Recalculate if missing
                trust_breakdown = await TrustService.recalculate_provider_trust(db, provider.id)
                t_score_val = trust_breakdown.trust_score

            trust_score_norm = min(100.0, max(0.0, t_score_val))

            # 6. Rating Score (10%)
            total_reviews = provider.total_reviews or 0
            if total_reviews < 3:
                rating_score_norm = 50.0  # neutral prior for <3 reviews
            else:
                rating_score_norm = min(100.0, (float(provider.average_rating or 0.0) / 5.0) * 100.0)

            # Weighted Total Score
            total_match_score = (
                service_score * 0.30
                + distance_score * 0.20
                + price_score * 0.15
                + availability_score * 0.15
                + trust_score_norm * 0.10
                + rating_score_norm * 0.10
            )
            total_match_score = round(total_match_score, 2)

            # Build Match Explanations
            explanations = []
            if service_score >= 80.0:
                explanations.append(f"✓ Provides {matching_service_name or 'requested service'}")
            else:
                explanations.append(f"✓ Related skills in {provider.display_name}'s profile")

            if distance_km is not None:
                explanations.append(f"✓ Within {distance_km:.1f} km")
            else:
                explanations.append("✓ Located in your service zone")

            if req_budget is not None and min_provider_price is not None:
                if min_provider_price <= req_budget:
                    explanations.append(f"✓ Within your ₹{int(req_budget)} budget")
                else:
                    explanations.append(f"✓ Pricing starting from ₹{int(min_provider_price)}")

            if availability_score >= 50.0:
                explanations.append("✓ Available on requested schedule")

            if trust_score_norm >= 60.0:
                explanations.append(f"✓ Strong trust score ({int(trust_score_norm)}%)")

            # Create or update match record
            existing_match_stmt = select(RequestMatch).where(
                RequestMatch.request_id == request_id,
                RequestMatch.provider_id == provider.id
            )
            ex_res = await db.execute(existing_match_stmt)
            match_rec = ex_res.scalar_one_or_none()

            now = datetime.now(timezone.utc)
            if not match_rec:
                match_rec = RequestMatch(
                    request_id=request_id,
                    provider_id=provider.id,
                    distance_km=distance_km,
                    service_score=service_score,
                    availability_score=availability_score,
                    price_score=price_score,
                    rating_score=rating_score_norm,
                    trust_score=trust_score_norm,
                    total_match_score=total_match_score,
                    status=MatchStatus.PENDING,
                    created_at=now,
                    updated_at=now,
                )
                db.add(match_rec)
            else:
                match_rec.distance_km = distance_km
                match_rec.service_score = service_score
                match_rec.availability_score = availability_score
                match_rec.price_score = price_score
                match_rec.rating_score = rating_score_norm
                match_rec.trust_score = trust_score_norm
                match_rec.total_match_score = total_match_score
                match_rec.updated_at = now

            matches.append((match_rec, provider, explanations))

        # Sort matches by highest total_match_score
        matches.sort(key=lambda x: x[0].total_match_score, reverse=True)

        # Update request status to MATCHED
        request_obj.status = RequestStatus.MATCHED
        request_obj.updated_at = datetime.now(timezone.utc)
        await db.flush()

        response_list: List[MatchResponse] = []
        for match_rec, provider, explanations in matches:
            provider_resp = ProviderResponse.model_validate(provider)
            provider_resp.trust_score = float(match_rec.trust_score)

            match_dto = MatchResponse(
                id=match_rec.id,
                request_id=match_rec.request_id,
                provider_id=match_rec.provider_id,
                distance_km=float(match_rec.distance_km) if match_rec.distance_km is not None else None,
                service_score=float(match_rec.service_score),
                availability_score=float(match_rec.availability_score),
                price_score=float(match_rec.price_score),
                rating_score=float(match_rec.rating_score),
                trust_score=float(match_rec.trust_score),
                total_match_score=float(match_rec.total_match_score),
                status=match_rec.status,
                provider_response=match_rec.provider_response,
                provider_responded_at=match_rec.provider_responded_at,
                created_at=match_rec.created_at,
                updated_at=match_rec.updated_at,
                provider=provider_resp,
                match_explanations=explanations,
            )
            response_list.append(match_dto)

        return response_list
