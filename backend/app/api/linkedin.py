import logging
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.deps import get_current_user
from app.api.helpers import get_user_job, get_user_profile, get_portfolio_projects, _json_load
from app.models.user import User
from app.models.job import Job, JobStatus
from app.models.linkedin import LinkedInMessage
from app.models.notification import NotificationType
from app.schemas.linkedin import LinkedInGenerateRequest, LinkedInUpdateRequest, LinkedInMessageResponse
from app.ai import get_ai_provider
from app.services import notification_service
from app.services.webhook_service import dispatch_webhook_event

logger = logging.getLogger(__name__)
router = APIRouter(tags=["linkedin"])


@router.post("/jobs/{job_id}/linkedin/generate", response_model=LinkedInMessageResponse)
async def generate_linkedin_messages(
    job_id: int, data: LinkedInGenerateRequest,
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db),
):
    """Generate both a LinkedIn Connection Request note (<= 300 chars) and InMail pitch."""
    job = get_user_job(db, job_id, current_user.id)
    profile = get_user_profile(db, current_user.id, required=False)
    projects = get_portfolio_projects(db, profile.id) if profile else []

    profile_dict = {
        "startup_name": profile.startup_name if profile else "Our Team",
        "description": profile.description if profile else "",
        "services": _json_load(profile.services) if profile else [],
    }

    projects_list = [
        {"id": p.id, "title": p.project_name, "description": p.description, "technologies": p.technologies}
        for p in projects
    ]

    job_dict = {
        "id": job.id, "title": job.title,
        "company": job.company or "Client",
        "description": job.description or "",
    }

    ai_provider = get_ai_provider()
    generated = await ai_provider.generate_linkedin_messages(
        job_details=job_dict, startup_profile=profile_dict,
        portfolio_projects=projects_list, recipient_name=data.recipient_name,
        recipient_role=data.recipient_role, tone=data.tone,
        custom_instructions=data.custom_instructions,
    )

    msg = LinkedInMessage(
        job_id=job.id, user_id=current_user.id,
        recipient_name=data.recipient_name, recipient_role=data.recipient_role,
        recipient_profile_url=data.recipient_profile_url, tone=data.tone,
        connection_note=generated["connection_note"],
        inmail_subject=generated["inmail_subject"],
        inmail_body=generated["inmail_body"], status="GENERATED",
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg


def _get_user_linkedin(db: Session, msg_id: int, user_id: int) -> LinkedInMessage:
    msg = db.query(LinkedInMessage).filter(LinkedInMessage.id == msg_id, LinkedInMessage.user_id == user_id).first()
    if not msg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="LinkedIn message not found")
    return msg


@router.get("/jobs/{job_id}/linkedin", response_model=List[LinkedInMessageResponse])
def get_job_linkedin_messages(
    job_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db),
):
    """Retrieve all LinkedIn messages for a specific job."""
    get_user_job(db, job_id, current_user.id)
    return db.query(LinkedInMessage).filter(
        LinkedInMessage.job_id == job_id, LinkedInMessage.user_id == current_user.id,
    ).order_by(LinkedInMessage.created_at.desc()).all()


@router.get("/linkedin/{id}", response_model=LinkedInMessageResponse)
def get_linkedin_message(id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Retrieve a single LinkedIn message by ID."""
    return _get_user_linkedin(db, id, current_user.id)


@router.put("/linkedin/{id}", response_model=LinkedInMessageResponse)
def update_linkedin_message(
    id: int, data: LinkedInUpdateRequest,
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db),
):
    """Edit connection note, InMail content, or recipient details."""
    msg = _get_user_linkedin(db, id, current_user.id)

    if data.recipient_name is not None:
        msg.recipient_name = data.recipient_name
    if data.recipient_role is not None:
        msg.recipient_role = data.recipient_role
    if data.recipient_profile_url is not None:
        msg.recipient_profile_url = data.recipient_profile_url
    if data.connection_note is not None:
        note = data.connection_note.strip()
        if len(note) > 300:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Connection note must be 300 characters or fewer.")
        msg.connection_note = note
    if data.inmail_subject is not None:
        msg.inmail_subject = data.inmail_subject
    if data.inmail_body is not None:
        msg.inmail_body = data.inmail_body

    db.commit()
    db.refresh(msg)
    return msg


@router.post("/linkedin/{id}/mark-sent", response_model=LinkedInMessageResponse)
async def mark_linkedin_sent(
    id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db),
):
    """Mark that outreach was sent via LinkedIn, advancing job status to CONTACTED."""
    msg = _get_user_linkedin(db, id, current_user.id)
    msg.status = "SENT"
    msg.sent_at = datetime.now(timezone.utc)


    job = db.query(Job).filter(Job.id == msg.job_id).first()
    if job:
        job.status = JobStatus.CONTACTED
        target = msg.recipient_name or job.company or "lead"
        notification_service.create_notification(
            db=db, user_id=current_user.id, type=NotificationType.OUTREACH_SENT,
            title="LinkedIn Outreach Marked as Sent",
            message=f"Outreach to {target} for '{job.title}' was marked as sent on LinkedIn.",
            job_id=job.id,
        )

    db.commit()
    db.refresh(msg)

    try:
        await dispatch_webhook_event(
            db=db, user_id=current_user.id, event_type="outreach.sent",
            payload={
                "channel": "linkedin", "job_id": msg.job_id,
                "linkedin_message_id": msg.id, "recipient_name": msg.recipient_name,
                "recipient_role": msg.recipient_role, "tone": msg.tone,
            },
        )
    except Exception as e:
        logger.warning(f"Failed to dispatch outreach.sent webhook: {e}")

    return msg


@router.delete("/linkedin/{id}")
def delete_linkedin_message(id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Delete a LinkedIn message record."""
    msg = _get_user_linkedin(db, id, current_user.id)
    db.delete(msg)
    db.commit()
    return {"message": "LinkedIn draft deleted successfully"}
