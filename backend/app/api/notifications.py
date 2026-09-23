"""
Notifications API endpoints (Phase 3).

GET    /api/notifications          — list recent notifications + unread count
GET    /api/notifications/count    — lightweight unread count poll
PATCH  /api/notifications/read-all — mark all as read
PATCH  /api/notifications/{id}/read — mark one as read
DELETE /api/notifications/all      — clear all notifications
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.notification import (
    NotificationResponse,
    NotificationCountResponse,
    NotificationListResponse,
)
from app.services import notification_service

router = APIRouter()


@router.get("/count", response_model=NotificationCountResponse)
def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Lightweight endpoint polled by the frontend every 30s."""
    count = notification_service.get_unread_count(db, current_user.id)
    return NotificationCountResponse(unread=count)


@router.get("/", response_model=NotificationListResponse)
def get_notifications(
    limit: int = 30,
    unread_only: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return recent notifications for the current user."""
    notifications = notification_service.get_notifications(
        db, current_user.id, limit=limit, unread_only=unread_only
    )
    unread = notification_service.get_unread_count(db, current_user.id)
    return NotificationListResponse(
        notifications=notifications,
        unread=unread,
    )


@router.patch("/read-all")
def mark_all_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark all notifications as read."""
    updated = notification_service.mark_all_read(db, current_user.id)
    return {"updated": updated, "message": f"{updated} notification(s) marked as read."}


@router.patch("/{notification_id}/read", response_model=NotificationResponse)
def mark_one_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark a single notification as read."""
    notif = notification_service.mark_read(db, current_user.id, notification_id)
    if not notif:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found.",
        )
    return notif


@router.delete("/all")
def clear_all(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete all notifications for the current user."""
    deleted = notification_service.clear_all(db, current_user.id)
    return {"deleted": deleted, "message": f"{deleted} notification(s) cleared."}
