import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, Field
from app.models.enums import RequestStatus


class RequirementParseResult(BaseModel):
    category: Optional[str] = None
    service: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    radius_km: Optional[float] = Field(default=5.0)
    availability: List[str] = Field(default_factory=list)
    level: Optional[str] = None
    preferences: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(default=0.9, ge=0.0, le=1.0)


class RequestCreate(BaseModel):
    raw_description: str = Field(min_length=3)
    category_id: Optional[uuid.UUID] = None
    service_id: Optional[uuid.UUID] = None
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    radius_km: float = 5.0
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class RequestUpdate(BaseModel):
    raw_description: Optional[str] = None
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    radius_km: Optional[float] = None
    status: Optional[RequestStatus] = None


class RequestResponse(BaseModel):
    id: uuid.UUID
    requester_id: uuid.UUID
    raw_description: str
    ai_parsed_requirement: Optional[Dict[str, Any]] = None
    ai_confidence: Optional[float] = None
    category_id: Optional[uuid.UUID] = None
    service_id: Optional[uuid.UUID] = None
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    radius_km: float
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    status: RequestStatus
    expires_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
