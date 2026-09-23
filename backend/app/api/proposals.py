"""
Proposals API endpoints (Phase 4).
"""
import json
import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.deps import get_current_user
from app.api.helpers import (
    get_user_job, get_user_profile, get_portfolio_projects,
    serialize_profile, serialize_projects,
)
from app.models.user import User
from app.models.job import Job, JobStatus
from app.models.proposal import Proposal, ProposalStatus
from app.models.portfolio_project import PortfolioProject
from app.models.notification import NotificationType
from app.schemas.proposal import ProposalGenerateRequest, ProposalUpdateRequest, ProposalResponse
from app.ai import get_ai_provider
from app.services import notification_service
from app.services.webhook_service import dispatch_webhook_event

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/jobs/{job_id}/proposals/generate", response_model=ProposalResponse, status_code=status.HTTP_201_CREATED)
async def generate_proposal(
    job_id: int,
    request: ProposalGenerateRequest = ProposalGenerateRequest(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate an AI-powered proposal for an opportunity."""
    job = get_user_job(db, job_id, current_user.id)
    profile = get_user_profile(db, current_user.id)

    portfolio_query = db.query(PortfolioProject).filter(PortfolioProject.startup_profile_id == profile.id)
    if request.include_portfolio_ids:
        portfolio_query = portfolio_query.filter(PortfolioProject.id.in_(request.include_portfolio_ids))
    portfolio_projects = portfolio_query.all()

    latest_proposal = db.query(Proposal).filter(Proposal.job_id == job_id).order_by(Proposal.version.desc()).first()
    next_version = (latest_proposal.version + 1) if latest_proposal else 1

    job_details = {
        "title": job.title, "company": job.company or "Client",
        "description": job.description, "location": job.location,
        "job_type": job.job_type,
        "salary_min": float(job.salary_min) if job.salary_min else None,
        "salary_max": float(job.salary_max) if job.salary_max else None,
        "currency": job.currency,
        "skills": json.loads(job.skills) if job.skills else [],
    }

    ai_provider = get_ai_provider()
    try:
        generated = await ai_provider.generate_proposal(
            job_details=job_details,
            startup_profile=serialize_profile(profile),
            portfolio_projects=serialize_projects(portfolio_projects),
            tone=request.tone,
            custom_instructions=request.custom_instructions,
        )
    except Exception as e:
        logger.error(f"Error generating proposal via AI: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Proposal generation failed: {e}")

    new_proposal = Proposal(
        job_id=job.id, user_id=current_user.id, version=next_version,
        title=generated.title, tone=request.tone, custom_instructions=request.custom_instructions,
        content=generated.content, cover_letter=generated.cover_letter,
        estimated_duration=generated.estimated_duration, estimated_budget=generated.estimated_budget,
        relevant_projects=json.dumps(generated.relevant_projects) if generated.relevant_projects else None,
        status=ProposalStatus.DRAFT,
    )
    db.add(new_proposal)
    job.status = JobStatus.PROPOSAL_READY
    db.commit()
    db.refresh(new_proposal)

    notification_service.create_notification(
        db=db, user_id=current_user.id, type=NotificationType.PROPOSAL_READY,
        title="Proposal Ready",
        message=f'Proposal draft (v{next_version}) for "{job.title}" has been generated.',
        job_id=job.id,
    )

    try:
        await dispatch_webhook_event(
            db=db, user_id=current_user.id, event_type="proposal.ready",
            payload={
                "job_id": job.id, "proposal_id": new_proposal.id,
                "version": new_proposal.version, "title": new_proposal.title,
                "tone": new_proposal.tone, "estimated_budget": new_proposal.estimated_budget,
            },
        )
    except Exception as e:
        logger.warning(f"Failed to dispatch proposal.ready webhook: {e}")

    return new_proposal


@router.get("/jobs/{job_id}/proposals", response_model=List[ProposalResponse])
def get_job_proposals(job_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get all proposal drafts for a specific job."""
    get_user_job(db, job_id, current_user.id)
    return db.query(Proposal).filter(
        Proposal.job_id == job_id, Proposal.user_id == current_user.id,
    ).order_by(Proposal.version.desc()).all()


def _get_user_proposal(db: Session, proposal_id: int, user_id: int) -> Proposal:
    proposal = db.query(Proposal).filter(Proposal.id == proposal_id, Proposal.user_id == user_id).first()
    if not proposal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proposal not found")
    return proposal


@router.get("/proposals/{proposal_id}", response_model=ProposalResponse)
def get_proposal(proposal_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get a specific proposal by ID."""
    return _get_user_proposal(db, proposal_id, current_user.id)


@router.put("/proposals/{proposal_id}", response_model=ProposalResponse)
def update_proposal(
    proposal_id: int, update_data: ProposalUpdateRequest,
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db),
):
    """Edit proposal content, cover letter, or metadata."""
    proposal = _get_user_proposal(db, proposal_id, current_user.id)
    for field, value in update_data.model_dump(exclude_unset=True).items():
        setattr(proposal, field, value)

    if update_data.status == ProposalStatus.APPROVED:
        job = db.query(Job).filter(Job.id == proposal.job_id).first()
        if job:
            job.status = JobStatus.PROPOSAL_APPROVED

    db.commit()
    db.refresh(proposal)
    return proposal


@router.post("/proposals/{proposal_id}/approve", response_model=ProposalResponse)
def approve_proposal(proposal_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Approve a proposal draft."""
    proposal = _get_user_proposal(db, proposal_id, current_user.id)
    proposal.status = ProposalStatus.APPROVED

    job = db.query(Job).filter(Job.id == proposal.job_id).first()
    if job:
        job.status = JobStatus.PROPOSAL_APPROVED

    db.commit()
    db.refresh(proposal)

    notification_service.create_notification(
        db=db, user_id=current_user.id, type=NotificationType.PROPOSAL_APPROVED,
        title="Proposal Approved",
        message=f'Proposal (v{proposal.version}) for "{job.title if job else "opportunity"}" was approved.',
        job_id=proposal.job_id,
    )
    return proposal


@router.post("/proposals/{proposal_id}/reject", response_model=ProposalResponse)
def reject_proposal(proposal_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Reject a proposal draft."""
    proposal = _get_user_proposal(db, proposal_id, current_user.id)
    proposal.status = ProposalStatus.REJECTED
    db.commit()
    db.refresh(proposal)
    return proposal
