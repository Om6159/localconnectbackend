import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from app.models.enums import MatchStatus
from app.schemas.provider import ProviderResponse


class MatchResponse(BaseModel):
    id: uuid.UUID
    request_id: uuid.UUID
    provider_id: uuid.UUID
    distance_km: Optional[float] = None
    service_score: float
    availability_score: float
    price_score: float
    rating_score: float
    trust_score: float
    total_match_score: float
    status: MatchStatus
    provider_response: Optional[str] = None
    provider_responded_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    # Rich details for UI display
    provider: Optional[ProviderResponse] = None
    match_explanations: List[str] = []

    model_config = ConfigDict(from_attributes=True)


class MatchRespondRequest(BaseModel):
    status: MatchStatus
    response_text: Optional[str] = None
