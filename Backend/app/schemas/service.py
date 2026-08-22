import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class ServiceBase(BaseModel):
    category_id: uuid.UUID
    name: str
    slug: str
    description: str | None = None
    base_price: float | None = None
    is_active: bool = True


class ServiceCreate(ServiceBase):
    pass


class ServiceResponse(ServiceBase):
    id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
