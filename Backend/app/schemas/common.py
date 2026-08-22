from typing import Generic, TypeVar, Optional, List
from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class StandardResponse(BaseModel, Generic[T]):
    success: bool = True
    data: Optional[T] = None
    message: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    size: int

    model_config = ConfigDict(from_attributes=True)
