import uuid
from datetime import datetime, timezone
from sqlalchemy import Text, DateTime, ForeignKey, Numeric, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base
from app.models.enums import MatchStatus


class RequestMatch(Base):
    __tablename__ = "request_matches"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    request_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("requests.id", ondelete="CASCADE"), nullable=False, index=True
    )
    provider_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("providers.id", ondelete="CASCADE"), nullable=False, index=True
    )

    distance_km: Mapped[float | None] = mapped_column(Numeric(8, 3), nullable=True)

    service_score: Mapped[float] = mapped_column(Numeric(5, 2), default=0.0, nullable=False)
    availability_score: Mapped[float] = mapped_column(Numeric(5, 2), default=0.0, nullable=False)
    price_score: Mapped[float] = mapped_column(Numeric(5, 2), default=0.0, nullable=False)
    rating_score: Mapped[float] = mapped_column(Numeric(5, 2), default=0.0, nullable=False)
    trust_score: Mapped[float] = mapped_column(Numeric(5, 2), default=0.0, nullable=False)

    total_match_score: Mapped[float] = mapped_column(Numeric(6, 2), default=0.0, nullable=False, index=True)

    status: Mapped[MatchStatus] = mapped_column(
        SQLEnum(MatchStatus, name="match_status"), default=MatchStatus.PENDING, nullable=False, index=True
    )

    provider_response: Mapped[str | None] = mapped_column(Text, nullable=True)
    provider_responded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

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
    request = relationship("Request", back_populates="matches")
    provider = relationship("Provider", back_populates="matches")
    connections = relationship("Connection", back_populates="match")
