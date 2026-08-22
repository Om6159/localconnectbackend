import uuid
from datetime import datetime, timezone
from sqlalchemy import Integer, Boolean, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class ProviderService(Base):
    __tablename__ = "provider_services"

    provider_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("providers.id", ondelete="CASCADE"), primary_key=True, index=True
    )
    service_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("services.id", ondelete="CASCADE"), primary_key=True, index=True
    )

    price_from: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    price_to: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)

    experience_years: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    provider = relationship("Provider", back_populates="services")
    service = relationship("Service", back_populates="provider_services")
