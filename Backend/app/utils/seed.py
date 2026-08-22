import asyncio
import uuid
from datetime import datetime, timezone, time
from sqlalchemy import select

from app.core.database import AsyncSessionLocal, engine, Base
from app.core.security import get_password_hash
from app.models import (
    Profile,
    Category,
    Service,
    Provider,
    ProviderService,
    Location,
    ProviderAvailability,
    Review,
)
from app.services.trust_service import TrustService


async def seed_database():
    """Populates database with realistic Indian local service sample data."""
    print("🌱 Starting database seeding...")

    # Create tables if not present (convenient for local sqlite/postgres demo)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        # 1. Categories
        cat_edu = Category(id=uuid.uuid4(), name="Education & Tutors", slug="education", description="Tutors, test prep, languages")
        cat_home = Category(id=uuid.uuid4(), name="Home Maintenance", slug="home-maintenance", description="Plumbing, electrical, cleaning")
        cat_tech = Category(id=uuid.uuid4(), name="Creative & Tech", slug="creative-tech", description="Designers, developers, photo/video")
        cat_event = Category(id=uuid.uuid4(), name="Events & Catering", slug="events-catering", description="Event planning, food, decoration")

        db.add_all([cat_edu, cat_home, cat_tech, cat_event])
        await db.flush()

        # 2. Services
        srv_math = Service(id=uuid.uuid4(), category_id=cat_edu.id, name="Math Tutor", slug="math-tutor", description="Class 8-12 Mathematics tutoring", base_price=500.0)
        srv_science = Service(id=uuid.uuid4(), category_id=cat_edu.id, name="Science Tutor", slug="science-tutor", description="Class 8-10 Science & Physics", base_price=600.0)
        srv_plumb = Service(id=uuid.uuid4(), category_id=cat_home.id, name="Plumbing", slug="plumbing", description="Tap repair, leak fixing, pipe fitting", base_price=350.0)
        srv_elec = Service(id=uuid.uuid4(), category_id=cat_home.id, name="Electrical Service", slug="electrical", description="Wiring, light installation, appliance repair", base_price=400.0)
        srv_design = Service(id=uuid.uuid4(), category_id=cat_tech.id, name="UI/UX Design", slug="ui-ux-design", description="Mobile app & web design", base_price=1200.0)
        srv_photo = Service(id=uuid.uuid4(), category_id=cat_tech.id, name="Photography", slug="photography", description="Event & portrait photography", base_price=2500.0)

        db.add_all([srv_math, srv_science, srv_plumb, srv_elec, srv_design, srv_photo])
        await db.flush()

        # 3. Requester User Profile
        user_req = Profile(
            id=uuid.uuid4(),
            email="user@localconnect.com",
            hashed_password=get_password_hash("password123"),
            full_name="Aarav Sharma",
            phone="+919876543210",
            bio="Looking for trusted local service providers in Mumbai.",
        )
        db.add(user_req)

        # 4. Providers
        # Provider 1: Ramesh Kumar (Math Tutor)
        prof_p1 = Profile(
            id=uuid.uuid4(),
            email="ramesh.maths@gmail.com",
            hashed_password=get_password_hash("provider123"),
            full_name="Ramesh Kumar",
            phone="+919820011223",
            bio="Experienced Math tutor with 8+ years teaching Class 10 & 12 CBSE/ICSE students.",
        )
        db.add(prof_p1)
        await db.flush()

        p1 = Provider(
            id=uuid.uuid4(),
            user_id=prof_p1.id,
            display_name="Ramesh Kumar Mathematics",
            bio="Specialized in Class 10 & 12 Board exam preparation with proven 90%+ score records.",
            experience_years=8,
            phone_verified_at=datetime.now(timezone.utc),
            identity_submitted_at=datetime.now(timezone.utc),
            recommendation_count=5,
            response_rate=95.0,
            completed_jobs=14,
            average_rating=4.9,
            total_reviews=12,
            service_radius_km=6.0,
            is_active=True,
        )
        db.add(p1)
        await db.flush()

        ps1 = ProviderService(provider_id=p1.id, service_id=srv_math.id, price_from=450.0, price_to=600.0, experience_years=8, is_primary=True)
        loc1 = Location(provider_id=p1.id, label="Home Office", city="Mumbai", locality="Bandra West", latitude=19.0596, longitude=72.8295, is_primary=True)
        db.add_all([ps1, loc1])

        # Provider 1 Availability (Sat & Sun)
        for day in [5, 6]:  # Saturday, Sunday
            db.add(ProviderAvailability(provider_id=p1.id, day_of_week=day, start_time=time(9, 0), end_time=time(18, 0), is_available=True))

        # Provider 2: Priya Patel (UI Designer)
        prof_p2 = Profile(
            id=uuid.uuid4(),
            email="priya.design@gmail.com",
            hashed_password=get_password_hash("provider123"),
            full_name="Priya Patel",
            phone="+919833344556",
            bio="Product designer crafting sleek mobile and web apps for local startups.",
        )
        db.add(prof_p2)
        await db.flush()

        p2 = Provider(
            id=uuid.uuid4(),
            user_id=prof_p2.id,
            display_name="Priya Design Studio",
            bio="Modern Figma designs, mobile UX design, and website landing pages.",
            experience_years=5,
            phone_verified_at=datetime.now(timezone.utc),
            identity_submitted_at=datetime.now(timezone.utc),
            recommendation_count=3,
            response_rate=90.0,
            completed_jobs=8,
            average_rating=4.8,
            total_reviews=6,
            service_radius_km=15.0,
            is_active=True,
        )
        db.add(p2)
        await db.flush()

        ps2 = ProviderService(provider_id=p2.id, service_id=srv_design.id, price_from=1000.0, price_to=2000.0, experience_years=5, is_primary=True)
        loc2 = Location(provider_id=p2.id, label="Studio", city="Mumbai", locality="Andheri East", latitude=19.1197, longitude=72.8464, is_primary=True)
        db.add_all([ps2, loc2])

        for day in range(0, 5):  # Mon-Fri
            db.add(ProviderAvailability(provider_id=p2.id, day_of_week=day, start_time=time(10, 0), end_time=time(19, 0), is_available=True))

        # Provider 3: Suresh Electricians
        prof_p3 = Profile(
            id=uuid.uuid4(),
            email="suresh.electric@gmail.com",
            hashed_password=get_password_hash("provider123"),
            full_name="Suresh Verma",
            phone="+919811122233",
            bio="Licensed electrician for home wiring, light fixtures, and emergency power fixes.",
        )
        db.add(prof_p3)
        await db.flush()

        p3 = Provider(
            id=uuid.uuid4(),
            user_id=prof_p3.id,
            display_name="Suresh Electrical Services",
            bio="Fast emergency electrician services within 30 minutes in Dadar & Worli area.",
            experience_years=10,
            phone_verified_at=datetime.now(timezone.utc),
            identity_submitted_at=None,
            recommendation_count=2,
            response_rate=100.0,
            completed_jobs=25,
            average_rating=4.7,
            total_reviews=18,
            service_radius_km=8.0,
            is_active=True,
        )
        db.add(p3)
        await db.flush()

        ps3 = ProviderService(provider_id=p3.id, service_id=srv_elec.id, price_from=300.0, price_to=500.0, experience_years=10, is_primary=True)
        loc3 = Location(provider_id=p3.id, label="Workshop", city="Mumbai", locality="Dadar", latitude=19.0178, longitude=72.8478, is_primary=True)
        db.add_all([ps3, loc3])

        for day in range(0, 7):  # All 7 days
            db.add(ProviderAvailability(provider_id=p3.id, day_of_week=day, start_time=time(8, 0), end_time=time(21, 0), is_available=True))

        await db.flush()

        # Recalculate trust scores for seeded providers
        await TrustService.recalculate_provider_trust(db, p1.id)
        await TrustService.recalculate_provider_trust(db, p2.id)
        await TrustService.recalculate_provider_trust(db, p3.id)

        await db.commit()
        print("✅ Seeding completed successfully!")


if __name__ == "__main__":
    asyncio.run(seed_database())
