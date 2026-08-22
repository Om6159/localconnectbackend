import uuid
from datetime import datetime, timezone
from sqlalchemy import Text, Float, DateTime, ForeignKey, Numeric, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from geoalchemy2 import Geography

from app.core.database import Base
from app.models.enums import RequestStatus


class Request(Base):
    __tablename__ = "requests"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    requester_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )

    raw_description: Mapped[str] = mapped_column(Text, nullable=False)
    ai_parsed_requirement: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    ai_confidence: Mapped[float | None] = mapped_column(Numeric(5, 4), nullable=True)

    category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, index=True
    )
    service_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("services.id", ondelete="SET NULL"), nullable=True, index=True
    )

    budget_min: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    budget_max: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)

    radius_km: Mapped[float] = mapped_column(Numeric(6, 2), default=5.0, nullable=False)

    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)

    location = mapped_column(
        Geography(geometry_type="POINT", srid=4326), nullable=True
    )

    status: Mapped[RequestStatus] = mapped_column(
        SQLEnum(RequestStatus, name="request_status"), default=RequestStatus.OPEN, nullable=False, index=True
    )

    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    requester = relationship("Profile", back_populates="requests")
    category = relationship("Category")
    service = relationship("Service")
    matches = relationship("RequestMatch", back_populates="request", cascade="all, delete-orphan")
    connections = relationship("Connection", back_populates="request", cascade="all, delete-orphan")
