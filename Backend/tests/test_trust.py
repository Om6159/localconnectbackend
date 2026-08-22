import pytest
import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.profile import Profile
from app.models.provider import Provider
from app.models.location import Location
from app.services.trust_service import TrustService


@pytest.mark.asyncio
async def test_canonical_trust_calculation(db_session: AsyncSession):
    # Create profile
    user = Profile(
        id=uuid.uuid4(),
        email="provider.trust@example.com",
        hashed_password="hash",
        full_name="Trust Provider",
    )
    db_session.add(user)
    await db_session.flush()

    # Create provider with verified phone & identity
    provider = Provider(
        id=uuid.uuid4(),
        user_id=user.id,
        display_name="Trust Test Provider",
        bio="Full bio description for test",
        experience_years=5,
        phone_verified_at=datetime.now(timezone.utc),
        identity_submitted_at=datetime.now(timezone.utc),
        completed_jobs=10,  # 10 * 5 = 50%
        recommendation_count=5,  # 5 * 10 = 50%
        response_rate=80.0,
        average_rating=4.5,
        total_reviews=5,  # >3 reviews, rating score = 90%
    )
    db_session.add(provider)
    await db_session.flush()

    # Primary location
    loc = Location(
        provider_id=provider.id,
        city="Mumbai",
        latitude=19.0760,
        longitude=72.8777,
        is_primary=True,
    )
    db_session.add(loc)
    await db_session.flush()

    breakdown = await TrustService.recalculate_provider_trust(db_session, provider.id)

    assert breakdown.phone_score == 100.0
    assert breakdown.identity_score == 100.0
    assert breakdown.completion_score == 50.0
    assert breakdown.recommendation_score == 50.0
    assert breakdown.response_score == 80.0
    assert breakdown.trust_score > 0.0
