import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from app.models.enums import ConnectionStatus
from app.schemas.provider import ProviderResponse
from app.schemas.profile import ProfileResponse


class ConnectionCreate(BaseModel):
    request_id: uuid.UUID
    provider_id: uuid.UUID
    match_id: Optional[uuid.UUID] = None


class ConnectionResponse(BaseModel):
    id: uuid.UUID
    request_id: uuid.UUID
    provider_id: uuid.UUID
    requester_id: uuid.UUID
    match_id: Optional[uuid.UUID] = None
    status: ConnectionStatus

    connected_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None

    requester_confirmed_at: Optional[datetime] = None
    provider_confirmed_at: Optional[datetime] = None

    created_at: datetime
    updated_at: datetime

    provider: Optional[ProviderResponse] = None
    requester: Optional[ProfileResponse] = None

    model_config = ConfigDict(from_attributes=True)
