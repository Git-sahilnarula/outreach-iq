"""
Email Outreach API endpoints (Phase 5).
"""
import logging
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.deps import get_current_user
from app.api.helpers import get_user_job
from app.models.user import User
from app.models.job import JobStatus
from app.models.outreach import OutreachMessage, OutreachStatus
from app.models.notification import NotificationType
from app.schemas.outreach import OutreachDraftCreate, OutreachUpdate, OutreachSendRequest, OutreachResponse
from app.integrations import gmail_client
from app.services import notification_service
from app.services.webhook_service import dispatch_webhook_event

logger = logging.getLogger(__name__)
router = APIRouter()


def _get_user_outreach(db: Session, outreach_id: int, user_id: int) -> OutreachMessage:
    outreach = db.query(OutreachMessage).filter(
        OutreachMessage.id == outreach_id, OutreachMessage.user_id == user_id,
    ).first()
    if not outreach:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Outreach record not found")
    return outreach


@router.post("/jobs/{job_id}/outreach/draft", response_model=OutreachResponse, status_code=status.HTTP_201_CREATED)
def create_outreach_draft(
    job_id: int, draft_data: OutreachDraftCreate,
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db),
):
    """Save an email outreach draft for a job opportunity."""
    job = get_user_job(db, job_id, current_user.id)
    new_outreach = OutreachMessage(
        job_id=job.id, user_id=current_user.id, proposal_id=draft_data.proposal_id,
        recipient_email=draft_data.recipient_email, recipient_name=draft_data.recipient_name,
        subject=draft_data.subject, body=draft_data.body, status=OutreachStatus.DRAFT,
    )
    db.add(new_outreach)
    db.commit()
    db.refresh(new_outreach)
    return new_outreach


@router.get("/jobs/{job_id}/outreach", response_model=List[OutreachResponse])
def get_job_outreach_history(
    job_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db),
):
    """List all outreach records for a specific job."""
    get_user_job(db, job_id, current_user.id)
    return db.query(OutreachMessage).filter(
        OutreachMessage.job_id == job_id, OutreachMessage.user_id == current_user.id,
    ).order_by(OutreachMessage.created_at.desc()).all()


@router.get("/outreach/{outreach_id}", response_model=OutreachResponse)
def get_outreach(outreach_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get a specific outreach message."""
    return _get_user_outreach(db, outreach_id, current_user.id)


@router.put("/outreach/{outreach_id}", response_model=OutreachResponse)
def update_outreach_draft(
    outreach_id: int, update_data: OutreachUpdate,
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db),
):
    """Update an unsent outreach draft."""
    outreach = _get_user_outreach(db, outreach_id, current_user.id)
    if outreach.status == OutreachStatus.SENT:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot edit a dispatched email.")

    for field, value in update_data.model_dump(exclude_unset=True).items():
        setattr(outreach, field, value)
    db.commit()
    db.refresh(outreach)
    return outreach


@router.post("/jobs/{job_id}/outreach/send", response_model=OutreachResponse)
async def send_outreach_email(
    job_id: int, send_data: OutreachSendRequest,
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db),
):
    """Send an outreach email via connected Gmail with human confirmation."""
    if not send_data.confirm_send:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Human approval required.")

    job = get_user_job(db, job_id, current_user.id)

    if not gmail_client.is_connected(db, current_user.id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Gmail is not connected.")

    try:
        send_result = gmail_client.send_email(
            db=db, user_id=current_user.id, to_email=send_data.recipient_email,
            subject=send_data.subject, body_text=send_data.body,
        )
    except Exception as e:
        logger.error(f"Failed to send email to {send_data.recipient_email}: {e}")
        failed = OutreachMessage(
            job_id=job.id, user_id=current_user.id, proposal_id=send_data.proposal_id,
            recipient_email=send_data.recipient_email, recipient_name=send_data.recipient_name,
            subject=send_data.subject, body=send_data.body,
            status=OutreachStatus.FAILED, error_message=str(e),
        )
        db.add(failed)
        db.commit()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Email dispatch failed: {e}")

    sent_outreach = OutreachMessage(
        job_id=job.id, user_id=current_user.id, proposal_id=send_data.proposal_id,
        recipient_email=send_data.recipient_email, recipient_name=send_data.recipient_name,
        subject=send_data.subject, body=send_data.body, status=OutreachStatus.SENT,
        gmail_message_id=send_result.get("id"), gmail_thread_id=send_result.get("threadId"),
        sent_at=datetime.now(timezone.utc),
    )
    db.add(sent_outreach)
    job.status = JobStatus.CONTACTED
    db.commit()
    db.refresh(sent_outreach)

    notification_service.create_notification(
        db=db, user_id=current_user.id, type=NotificationType.OUTREACH_SENT,
        title="Outreach Email Sent",
        message=f'Outreach sent to {send_data.recipient_email} for "{job.title}".',
        job_id=job.id,
    )

    try:
        await dispatch_webhook_event(
            db=db, user_id=current_user.id, event_type="outreach.sent",
            payload={
                "channel": "email", "job_id": job.id, "outreach_id": sent_outreach.id,
                "recipient_email": send_data.recipient_email,
                "recipient_name": send_data.recipient_name, "subject": send_data.subject,
            },
        )
    except Exception as e:
        logger.warning(f"Failed to dispatch outreach.sent webhook: {e}")

    return sent_outreach


@router.delete("/outreach/{outreach_id}")
def delete_outreach_draft(
    outreach_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db),
):
    """Delete an unsent draft message."""
    outreach = _get_user_outreach(db, outreach_id, current_user.id)
    if outreach.status == OutreachStatus.SENT:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete a dispatched email.")
    db.delete(outreach)
    db.commit()
    return {"message": "Draft deleted successfully"}
