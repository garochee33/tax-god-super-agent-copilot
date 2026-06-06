"""
Tax God - Notifications REST Endpoints
"""

from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import func, select, update

from app.api.deps import CurrentUser, DBSession
from app.models.notification import Notification

router = APIRouter()


@router.get("/notifications")
async def list_notifications(db: DBSession, user: CurrentUser):
    result = await db.execute(
        select(Notification)
        .where(Notification.user_id == user.id)
        .order_by(Notification.created_at.desc())
        .limit(50)
    )
    rows = result.scalars().all()
    return [
        {
            "id": n.id,
            "event_type": n.event_type,
            "title": n.title,
            "message": n.message,
            "data": n.data,
            "is_read": n.is_read,
            "created_at": n.created_at.isoformat(),
        }
        for n in rows
    ]


@router.patch("/notifications/{notification_id}/read")
async def mark_read(notification_id: str, db: DBSession, user: CurrentUser):
    await db.execute(
        update(Notification)
        .where(Notification.id == notification_id, Notification.user_id == user.id)
        .values(is_read=True)
    )
    await db.commit()
    return {"status": "ok"}


@router.get("/notifications/unread-count")
async def unread_count(db: DBSession, user: CurrentUser):
    result = await db.execute(
        select(func.count())
        .select_from(Notification)
        .where(Notification.user_id == user.id, Notification.is_read == False)  # noqa: E712
    )
    return {"unread_count": result.scalar()}
