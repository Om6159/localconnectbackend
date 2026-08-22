import uuid
from datetime import datetime, time
from pydantic import BaseModel, ConfigDict, Field


class AvailabilityBase(BaseModel):
    day_of_week: int = Field(ge=0, le=6)  # 0=Monday, 6=Sunday
    start_time: time
    end_time: time
    is_available: bool = True


class AvailabilityCreate(AvailabilityBase):
    pass


class AvailabilityResponse(AvailabilityBase):
    id: uuid.UUID
    provider_id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
