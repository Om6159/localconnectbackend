import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class CommunityRecommendationCreate(BaseModel):
    connection_id: uuid.UUID


class CommunityRecommendationResponse(BaseModel):
    id: uuid.UUID
    recommender_id: uuid.UUID
    provider_id: uuid.UUID
    connection_id: uuid.UUID
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
