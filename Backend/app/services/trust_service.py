import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.models.provider import Provider
from app.models.trust import ProviderTrustScore
from app.models.provider_service import ProviderService
from app.models.availability import ProviderAvailability
from app.models.location import Location
from app.schemas.trust import TrustScoreBreakdown


class TrustService:
    @staticmethod
    async def recalculate_provider_trust(
        db: AsyncSession, provider_id: uuid.UUID
    ) -> TrustScoreBreakdown:
        """
        Recalculates the Canonical Trust Score for a provider based on the documented formula:
        Phone (15%) + Identity (10%) + Profile (15%) + Rating (20%) + Completion (15%) + Recommendation (10%) + Response (15%)
        """
        # Fetch provider with loaded user relationship
        stmt = (
            select(Provider)
            .where(Provider.id == provider_id)
            .options(selectinload(Provider.user))
        )
        res = await db.execute(stmt)
        provider = res.scalar_one_or_none()
        if not provider:
            raise ValueError("Provider not found")

        # 1. Phone Score (15%): Binary
        phone_score = 100.0 if provider.phone_verified_at is not None else 0.0

        # 2. Identity Score (10%): Binary
        identity_score = 100.0 if provider.identity_submitted_at is not None else 0.0

        # 3. Profile Score (15%): Count of 7 fields filled
        fields_filled = 0
        if provider.display_name and len(provider.display_name.strip()) > 0:
            fields_filled += 1
        if provider.bio and len(provider.bio.strip()) > 0:
            fields_filled += 1
        if provider.service_radius_km and provider.service_radius_km > 0:
            fields_filled += 1

        # Check services
        ps_stmt = select(func.count()).select_from(ProviderService).where(ProviderService.provider_id == provider_id)
        services_cnt = (await db.execute(ps_stmt)).scalar() or 0
        if services_cnt > 0:
            fields_filled += 1

        # Check availability
        pa_stmt = select(func.count()).select_from(ProviderAvailability).where(ProviderAvailability.provider_id == provider_id)
        avail_cnt = (await db.execute(pa_stmt)).scalar() or 0
        if avail_cnt > 0:
            fields_filled += 1

        # Check primary location
        loc_stmt = select(func.count()).select_from(Location).where(
            Location.provider_id == provider_id, Location.is_primary == True
        )
        loc_cnt = (await db.execute(loc_stmt)).scalar() or 0
        if loc_cnt > 0:
            fields_filled += 1

        # Check user avatar / provider bio
        if provider.user and provider.user.avatar_url:
            fields_filled += 1
        elif provider.bio:
            fields_filled += 1

        profile_score = min(100.0, (fields_filled / 7.0) * 100.0)

        # 4. Rating Score (20%): Dampened below 3 reviews
        total_reviews = provider.total_reviews or 0
        avg_rating = float(provider.average_rating or 0.0)
        if total_reviews == 0:
            rating_score = 0.0
        elif total_reviews < 3:
            rating_score = 50.0  # Neutral prior
        else:
            rating_score = min(100.0, (avg_rating / 5.0) * 100.0)

        # 5. Completion Score (15%): Cap at 20 jobs (20 * 5 = 100)
        completion_score = min(100.0, float(provider.completed_jobs or 0) * 5.0)

        # 6. Recommendation Score (10%): Cap at 10 recommendations (10 * 10 = 100)
        recommendation_score = min(100.0, float(provider.recommendation_count or 0) * 10.0)

        # 7. Response Score (15%): Response rate directly
        response_score = min(100.0, float(provider.response_rate or 0.0))

        # Final Trust Score Calculation
        total_trust = (
            phone_score * 0.15
            + identity_score * 0.10
            + profile_score * 0.15
            + rating_score * 0.20
            + completion_score * 0.15
            + recommendation_score * 0.10
            + response_score * 0.15
        )
        total_trust = round(total_trust, 2)

        # Update or Insert provider_trust_scores
        ts_stmt = select(ProviderTrustScore).where(ProviderTrustScore.provider_id == provider_id)
        ts_res = await db.execute(ts_stmt)
        trust_record = ts_res.scalar_one_or_none()

        now = datetime.now(timezone.utc)
        if not trust_record:
            trust_record = ProviderTrustScore(
                provider_id=provider_id,
                phone_score=phone_score,
                identity_score=identity_score,
                profile_score=profile_score,
                rating_score=rating_score,
                completion_score=completion_score,
                recommendation_score=recommendation_score,
                response_score=response_score,
                trust_score=total_trust,
                calculation_version="v2",
                calculated_at=now,
            )
            db.add(trust_record)
        else:
            trust_record.phone_score = phone_score
            trust_record.identity_score = identity_score
            trust_record.profile_score = profile_score
            trust_record.rating_score = rating_score
            trust_record.completion_score = completion_score
            trust_record.recommendation_score = recommendation_score
            trust_record.response_score = response_score
            trust_record.trust_score = total_trust
            trust_record.calculated_at = now

        await db.flush()

        return TrustScoreBreakdown(
            provider_id=provider_id,
            phone_score=phone_score,
            identity_score=identity_score,
            profile_score=profile_score,
            rating_score=rating_score,
            completion_score=completion_score,
            recommendation_score=recommendation_score,
            response_score=response_score,
            trust_score=total_trust,
            calculation_version="v2",
            calculated_at=now,
        )
