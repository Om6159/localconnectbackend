import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.profile import ProfileResponse


class ReviewCreate(BaseModel):
    rating: int = Field(ge=1, le=5)
    review_text: Optional[str] = None


class ReviewResponse(BaseModel):
    id: uuid.UUID
    connection_id: uuid.UUID
    reviewer_id: uuid.UUID
    reviewee_provider_id: uuid.UUID
    rating: int
    review_text: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    reviewer: Optional[ProfileResponse] = None

    model_config = ConfigDict(from_attributes=True)
