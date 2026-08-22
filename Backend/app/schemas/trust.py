import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class TrustScoreBreakdown(BaseModel):
    provider_id: uuid.UUID
    phone_score: float  # 15%
    identity_score: float  # 10%
    profile_score: float  # 15%
    rating_score: float  # 20%
    completion_score: float  # 15%
    recommendation_score: float  # 10%
    response_score: float  # 15%
    trust_score: float  # Total 100%
    calculation_version: str = "v2"
    calculated_at: datetime

    model_config = ConfigDict(from_attributes=True)
