import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class ProviderTrustScore(Base):
    __tablename__ = "provider_trust_scores"

    provider_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("providers.id", ondelete="CASCADE"), primary_key=True
    )

    phone_score: Mapped[float] = mapped_column(Numeric(5, 2), default=0.0, nullable=False)
    identity_score: Mapped[float] = mapped_column(Numeric(5, 2), default=0.0, nullable=False)
    profile_score: Mapped[float] = mapped_column(Numeric(5, 2), default=0.0, nullable=False)
    rating_score: Mapped[float] = mapped_column(Numeric(5, 2), default=0.0, nullable=False)
    completion_score: Mapped[float] = mapped_column(Numeric(5, 2), default=0.0, nullable=False)
    recommendation_score: Mapped[float] = mapped_column(Numeric(5, 2), default=0.0, nullable=False)
    response_score: Mapped[float] = mapped_column(Numeric(5, 2), default=0.0, nullable=False)

    trust_score: Mapped[float] = mapped_column(Numeric(5, 2), default=0.0, nullable=False, index=True)

    calculation_version: Mapped[str] = mapped_column(String(50), default="v2", nullable=False)

    calculated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    provider = relationship("Provider", back_populates="trust_score")
