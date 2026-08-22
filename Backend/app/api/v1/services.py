import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.service import Service
from app.schemas.service import ServiceResponse
from app.schemas.common import StandardResponse

router = APIRouter(prefix="/services", tags=["Services"])


@router.get("", response_model=StandardResponse[List[ServiceResponse]])
async def list_services(
    category_id: Optional[uuid.UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """List services, optionally filtered by category."""
    stmt = select(Service).where(Service.is_active == True)
    if category_id:
        stmt = stmt.where(Service.category_id == category_id)

    res = await db.execute(stmt)
    services = res.scalars().all()
    dtos = [ServiceResponse.model_validate(s) for s in services]
    return StandardResponse(data=dtos)
