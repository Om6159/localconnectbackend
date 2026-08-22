import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from app.models.enums import NotificationType


class NotificationResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    type: NotificationType
    title: str
    message: str
    reference_id: Optional[uuid.UUID] = None
    is_read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
