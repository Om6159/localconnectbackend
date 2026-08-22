import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class LocationBase(BaseModel):
    label: str = "Primary"
    locality: str | None = None
    city: str
    state: str | None = None
    pincode: str | None = None
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    is_primary: bool = True


class LocationCreate(LocationBase):
    pass


class LocationResponse(LocationBase):
    id: uuid.UUID
    user_id: uuid.UUID | None = None
    provider_id: uuid.UUID | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
