import uuid
from datetime import datetime, timezone
from sqlalchemy import Text, Integer, Boolean, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class Provider(Base):
    __tablename__ = "providers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), unique=True, nullable=False, index=True
    )
    display_name: Mapped[str] = mapped_column(Text, nullable=False)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    experience_years: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    phone_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    identity_submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    recommendation_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    response_rate: Mapped[float] = mapped_column(Numeric(5, 2), default=0.0, nullable=False)
    completed_jobs: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    average_rating: Mapped[float] = mapped_column(Numeric(3, 2), default=0.0, nullable=False, index=True)
    total_reviews: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    service_radius_km: Mapped[float] = mapped_column(Numeric(6, 2), default=5.0, nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    user = relationship("Profile", back_populates="provider")
    services = relationship("ProviderService", back_populates="provider", cascade="all, delete-orphan")
    locations = relationship("Location", back_populates="provider", cascade="all, delete-orphan")
    availabilities = relationship("ProviderAvailability", back_populates="provider", cascade="all, delete-orphan")
    trust_score = relationship("ProviderTrustScore", back_populates="provider", uselist=False, cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="reviewee_provider", cascade="all, delete-orphan")
    matches = relationship("RequestMatch", back_populates="provider", cascade="all, delete-orphan")
    connections = relationship("Connection", back_populates="provider", cascade="all, delete-orphan")
    community_recommendations = relationship("ProviderRecommendation", back_populates="provider", cascade="all, delete-orphan")
