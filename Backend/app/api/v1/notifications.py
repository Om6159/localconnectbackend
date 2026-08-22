import uuid
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.exceptions import NotFoundException, ForbiddenException
from app.models.profile import Profile
from app.models.notification import Notification
from app.schemas.notification import NotificationResponse
from app.schemas.common import StandardResponse
from app.api.deps import get_current_user

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=StandardResponse[List[NotificationResponse]])
async def list_notifications(
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    """List authenticated user's notifications."""
    stmt = select(Notification).where(Notification.user_id == current_user.id).order_by(Notification.created_at.desc())
    res = await db.execute(stmt)
    notifications = res.scalars().all()
    dtos = [NotificationResponse.model_validate(n) for n in notifications]
    return StandardResponse(data=dtos)


@router.patch("/{notification_id}/read", response_model=StandardResponse[NotificationResponse])
async def mark_notification_read(
    notification_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    """Mark notification as read."""
    stmt = select(Notification).where(Notification.id == notification_id)
    res = await db.execute(stmt)
    notif = res.scalar_one_or_none()

    if not notif:
        raise NotFoundException("Notification not found")
    if notif.user_id != current_user.id:
        raise ForbiddenException("Unauthorized to modify notification")

    notif.is_read = True
    await db.flush()

    return StandardResponse(data=NotificationResponse.model_validate(notif), message="Notification marked as read")
