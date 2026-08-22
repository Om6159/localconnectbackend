import uuid
from datetime import datetime
from typing import List, Optional, Any
from pydantic import BaseModel, ConfigDict, field_validator

from app.schemas.location import LocationResponse
from app.schemas.availability import AvailabilityResponse
from app.schemas.service import ServiceResponse


class ProviderServiceCreate(BaseModel):
    service_id: uuid.UUID
    price_from: Optional[float] = None
    price_to: Optional[float] = None
    experience_years: int = 0
    is_primary: bool = False


class ProviderServiceResponse(BaseModel):
    provider_id: uuid.UUID
    service_id: uuid.UUID
    price_from: Optional[float] = None
    price_to: Optional[float] = None
    experience_years: int
    is_primary: bool
    service: Optional[ServiceResponse] = None

    model_config = ConfigDict(from_attributes=True)


class ProviderCreate(BaseModel):
    display_name: str
    bio: Optional[str] = None
    experience_years: int = 0
    service_radius_km: float = 5.0
    services: Optional[List[ProviderServiceCreate]] = None
    location: Optional[dict] = None  # city, latitude, longitude, etc.


class ProviderUpdate(BaseModel):
    display_name: Optional[str] = None
    bio: Optional[str] = None
    experience_years: Optional[int] = None
    service_radius_km: Optional[float] = None
    is_active: Optional[bool] = None


class ProviderResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    display_name: str
    bio: Optional[str] = None
    experience_years: int
    phone_verified_at: Optional[datetime] = None
    identity_submitted_at: Optional[datetime] = None
    recommendation_count: int
    response_rate: float
    completed_jobs: int
    average_rating: float
    total_reviews: int
    service_radius_km: float
    is_active: bool
    created_at: datetime
    updated_at: datetime

    # Associated nested objects
    services: List[ProviderServiceResponse] = []
    locations: List[LocationResponse] = []
    availabilities: List[AvailabilityResponse] = []
    trust_score: Optional[float] = None

    @field_validator("trust_score", mode="before")
    @classmethod
    def convert_trust_score(cls, v: Any) -> Optional[float]:
        if v is None:
            return None
        if hasattr(v, "trust_score"):
            return float(v.trust_score)
        try:
            return float(v)
        except (ValueError, TypeError):
            return None

    model_config = ConfigDict(from_attributes=True)
