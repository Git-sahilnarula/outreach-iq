"""
Notification service.

Provides helpers to create, list, and manage in-app notifications.
Called from API routers when jobs are created, analysed, approved, or rejected.
"""
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.notification import Notification, NotificationType


def create_notification(
    db: Session,
    user_id: int,
    type: NotificationType,
    title: str,
    message: str,
    job_id: Optional[int] = None,
) -> Notification:
    """Insert a new notification for a user."""
    notif = Notification(
        user_id=user_id,
        type=type.value,
        title=title,
        message=message,
        job_id=job_id,
        read=False,
    )
    db.add(notif)
    db.commit()
    db.refresh(notif)
    return notif


def get_unread_count(db: Session, user_id: int) -> int:
    """Return the number of unread notifications for a user."""
    return db.query(Notification).filter(
        Notification.user_id == user_id,
        Notification.read == False,
    ).count()


def get_notifications(
    db: Session,
    user_id: int,
    limit: int = 30,
    unread_only: bool = False,
) -> List[Notification]:
    """Return recent notifications, newest first."""
    q = db.query(Notification).filter(Notification.user_id == user_id)
    if unread_only:
        q = q.filter(Notification.read == False)
    return q.order_by(Notification.created_at.desc(), Notification.id.desc()).limit(limit).all()


def mark_read(db: Session, user_id: int, notification_id: int) -> Optional[Notification]:
    """Mark a single notification as read. Returns None if not found/not owned."""
    notif = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == user_id,
    ).first()
    if notif:
        notif.read = True
        db.commit()
        db.refresh(notif)
    return notif


def mark_all_read(db: Session, user_id: int) -> int:
    """Mark all notifications as read. Returns count updated."""
    updated = db.query(Notification).filter(
        Notification.user_id == user_id,
        Notification.read == False,
    ).update({"read": True})
    db.commit()
    return updated


def clear_all(db: Session, user_id: int) -> int:
    """Delete all notifications for a user. Returns count deleted."""
    deleted = db.query(Notification).filter(
        Notification.user_id == user_id,
    ).delete()
    db.commit()
    return deleted
