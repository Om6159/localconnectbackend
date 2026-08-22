import uuid
from typing import List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.exceptions import NotFoundException, ForbiddenException, ConflictException, BadRequestException
from app.models.profile import Profile
from app.models.provider import Provider
from app.models.connection import Connection
from app.models.review import Review
from app.models.enums import ConnectionStatus
from app.schemas.review import ReviewCreate, ReviewResponse
from app.schemas.profile import ProfileResponse
from app.schemas.common import StandardResponse
from app.api.deps import get_current_user
from app.services.trust_service import TrustService

router = APIRouter(tags=["Reviews"])


@router.post("/connections/{connection_id}/review", response_model=StandardResponse[ReviewResponse], status_code=status.HTTP_201_CREATED)
async def submit_review(
    connection_id: uuid.UUID,
    payload: ReviewCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    """
    Submit a review for a completed connection.
    Recalculates provider rating & trust score upon submission.
    """
    # 1. Fetch connection
    conn_stmt = select(Connection).where(Connection.id == connection_id)
    conn = (await db.execute(conn_stmt)).scalar_one_or_none()

    if not conn:
        raise NotFoundException("Connection not found")

    if conn.status != ConnectionStatus.COMPLETED:
        raise BadRequestException("Reviews can only be submitted for completed connections")

    # Check participant
    prov_stmt = select(Provider).where(Provider.user_id == current_user.id)
    user_provider = (await db.execute(prov_stmt)).scalar_one_or_none()
    user_provider_id = user_provider.id if user_provider else None

    if conn.requester_id != current_user.id and conn.provider_id != user_provider_id:
        raise ForbiddenException("Only participants in this completed connection can leave a review")

    # Prevent duplicate review
    existing_rev_stmt = select(Review).where(
        Review.connection_id == connection_id,
        Review.reviewer_id == current_user.id,
    )
    if (await db.execute(existing_rev_stmt)).scalar_one_or_none():
        raise ConflictException("You have already reviewed this connection")

    reviewee_id = conn.provider_id if current_user.id == conn.requester_id else conn.requester_id

    review = Review(
        connection_id=connection_id,
        reviewer_id=current_user.id,
        reviewee_provider_id=conn.provider_id,
        rating=payload.rating,
        review_text=payload.review_text,
    )
    db.add(review)
    await db.flush()

    # Update provider average rating & total reviews
    provider_stmt = select(Provider).where(Provider.id == conn.provider_id)
    provider_obj = (await db.execute(provider_stmt)).scalar_one()

    avg_rating_res = await db.execute(
        select(func.avg(Review.rating), func.count(Review.id)).where(Review.reviewee_provider_id == conn.provider_id)
    )
    new_avg, new_count = avg_rating_res.one()

    provider_obj.average_rating = round(float(new_avg or 0.0), 2)
    provider_obj.total_reviews = int(new_count or 0)
    await db.flush()

    # Recalculate provider trust score
    await TrustService.recalculate_provider_trust(db, conn.provider_id)

    # Return created review
    loaded_rev = (
        await db.execute(
            select(Review).where(Review.id == review.id).options(selectinload(Review.reviewer))
        )
    ).scalar_one()

    dto = ReviewResponse.model_validate(loaded_rev)
    dto.reviewer = ProfileResponse.model_validate(loaded_rev.reviewer)
    return StandardResponse(data=dto, message="Review submitted successfully")


@router.get("/providers/{provider_id}/reviews", response_model=StandardResponse[List[ReviewResponse]])
async def list_provider_reviews(
    provider_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """List reviews for a provider."""
    stmt = (
        select(Review)
        .where(Review.reviewee_provider_id == provider_id)
        .order_by(Review.created_at.desc())
        .options(selectinload(Review.reviewer))
    )
    res = await db.execute(stmt)
    reviews = res.scalars().all()

    dtos = []
    for r in reviews:
        dto = ReviewResponse.model_validate(r)
        dto.reviewer = ProfileResponse.model_validate(r.reviewer) if r.reviewer else None
        dtos.append(dto)

    return StandardResponse(data=dtos)
