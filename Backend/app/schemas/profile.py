import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict


class ProfileBase(BaseModel):
    full_name: str
    avatar_url: str | None = None
    phone: str | None = None
    bio: str | None = None


class ProfileUpdate(BaseModel):
    full_name: str | None = None
    avatar_url: str | None = None
    phone: str | None = None
    bio: str | None = None


class ProfileResponse(ProfileBase):
    id: uuid.UUID
    email: EmailStr
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
