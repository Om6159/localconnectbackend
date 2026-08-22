from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.category import Category
from app.schemas.category import CategoryResponse
from app.schemas.common import StandardResponse

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get("", response_model=StandardResponse[List[CategoryResponse]])
async def list_categories(
    db: AsyncSession = Depends(get_db),
):
    """List all active service categories."""
    stmt = select(Category).where(Category.is_active == True)
    res = await db.execute(stmt)
    categories = res.scalars().all()
    dtos = [CategoryResponse.model_validate(c) for c in categories]
    return StandardResponse(data=dtos)
