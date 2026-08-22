import uuid
from datetime import datetime, timezone
from sqlalchemy import Text, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from geoalchemy2 import Geography

from app.core.database import Base


class Location(Base):
    __tablename__ = "locations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=True, index=True
    )
    provider_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("providers.id", ondelete="CASCADE"), nullable=True, index=True
    )

    label: Mapped[str] = mapped_column(Text, default="Primary", nullable=False)

    locality: Mapped[str | None] = mapped_column(Text, nullable=True)
    city: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    state: Mapped[str | None] = mapped_column(Text, nullable=True)
    pincode: Mapped[str | None] = mapped_column(Text, nullable=True)

    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)

    point = mapped_column(
        Geography(geometry_type="POINT", srid=4326), nullable=True
    )

    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    user = relationship("Profile", back_populates="locations")
    provider = relationship("Provider", back_populates="locations")
