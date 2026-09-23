import json
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.job import Job, JobStatus
from app.models.job_analysis import JobAnalysis
from app.models.user import User
from app.models.notification import NotificationType
from app.schemas.job import JobCreate, JobResponse
from app.schemas.job_analysis import JobAnalysisResponse
from app.api.deps import get_current_user
from app.api.helpers import (
    get_user_job, get_user_profile, get_portfolio_projects,
    serialize_profile, serialize_projects, serialize_analysis_fields,
)
from app.services.duplicate_detection import check_duplicate
from app.services import notification_service
from app.services.webhook_service import dispatch_webhook_event
from app.ai import get_ai_provider
from app.config import settings

router = APIRouter()


@router.post("/", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
def create_job(
    job: JobCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new job opportunity."""
    job_data = job.model_dump()
    existing_job = check_duplicate(db, current_user.id, job_data)
    if existing_job:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This job opportunity already exists",
            headers={"X-Existing-Job-ID": str(existing_job.id)},
        )

    if job_data.get("skills") is not None:
        job_data["skills"] = json.dumps(job_data["skills"])

    new_job = Job(user_id=current_user.id, **job_data)
    db.add(new_job)
    db.commit()
    db.refresh(new_job)

    notification_service.create_notification(
        db=db, user_id=current_user.id, type=NotificationType.NEW_JOB,
        title="New Job Added",
        message=f'"{new_job.title}" at {new_job.company or "Unknown Company"} has been added.',
        job_id=new_job.id,
    )
    return new_job


@router.get("/", response_model=List[JobResponse])
def get_jobs(
    skip: int = 0, limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all jobs for the current user."""
    return (
        db.query(Job).filter(Job.user_id == current_user.id)
        .order_by(Job.created_at.desc()).offset(skip).limit(limit).all()
    )


@router.get("/{job_id}", response_model=JobResponse)
def get_job(job_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get a specific job by ID."""
    return get_user_job(db, job_id, current_user.id)


@router.post("/{job_id}/analyze", response_model=JobAnalysisResponse)
async def analyze_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Analyze a job opportunity using AI."""
    job = get_user_job(db, job_id, current_user.id)
    profile = get_user_profile(db, current_user.id)
    projects = get_portfolio_projects(db, profile.id)

    job.status = JobStatus.ANALYZING
    db.commit()

    try:
        ai_provider = get_ai_provider()
        analysis_result = await ai_provider.analyze_opportunity(
            job_description=job.description,
            startup_profile=serialize_profile(profile),
            portfolio_projects=serialize_projects(projects),
        )

        analysis_data = serialize_analysis_fields(analysis_result.model_dump())

        existing_analysis = db.query(JobAnalysis).filter(JobAnalysis.job_id == job_id).first()
        if existing_analysis:
            for field, value in analysis_data.items():
                setattr(existing_analysis, field, value)
            db.commit()
            db.refresh(existing_analysis)
            analysis = existing_analysis
        else:
            analysis = JobAnalysis(job_id=job_id, **analysis_data)
            db.add(analysis)
            db.commit()
            db.refresh(analysis)

        job.status = JobStatus.REVIEW_REQUIRED if analysis.match_score >= settings.MATCH_THRESHOLD else JobStatus.REJECTED
        db.commit()

        if job.status == JobStatus.REVIEW_REQUIRED:
            notification_service.create_notification(
                db=db, user_id=current_user.id, type=NotificationType.REVIEW_REQUIRED,
                title="High Match — Review Required",
                message=f'"{job.title}" scored {analysis.match_score}/100. Ready for your review.',
                job_id=job.id,
            )
            try:
                await dispatch_webhook_event(
                    db=db, user_id=current_user.id, event_type="job.high_match",
                    payload={"job_id": job.id, "title": job.title, "company": job.company, "match_score": analysis.match_score},
                )
            except Exception:
                pass
        else:
            notification_service.create_notification(
                db=db, user_id=current_user.id, type=NotificationType.ANALYSIS_COMPLETE,
                title="Analysis Complete",
                message=f'"{job.title}" scored {analysis.match_score}/100 — below threshold, marked rejected.',
                job_id=job.id,
            )
        return analysis

    except Exception as e:
        job.status = JobStatus.NEW
        db.commit()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Analysis failed: {e}")


@router.get("/{job_id}/analysis", response_model=JobAnalysisResponse)
def get_job_analysis(job_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get analysis for a specific job."""
    get_user_job(db, job_id, current_user.id)
    analysis = db.query(JobAnalysis).filter(JobAnalysis.job_id == job_id).first()
    if not analysis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found for this job")
    return analysis


@router.post("/{job_id}/approve", response_model=JobResponse)
def approve_job(job_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Approve a job opportunity."""
    job = get_user_job(db, job_id, current_user.id)
    if job.status == JobStatus.APPROVED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Job is already approved.")

    job.status = JobStatus.APPROVED
    db.commit()
    db.refresh(job)

    notification_service.create_notification(
        db=db, user_id=current_user.id, type=NotificationType.JOB_APPROVED,
        title="Job Approved",
        message=f'You approved "{job.title}" at {job.company or "Unknown Company"}.',
        job_id=job.id,
    )
    return job


@router.post("/{job_id}/reject", response_model=JobResponse)
def reject_job(job_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Reject a job opportunity."""
    job = get_user_job(db, job_id, current_user.id)
    if job.status == JobStatus.REJECTED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Job is already rejected.")

    job.status = JobStatus.REJECTED
    db.commit()
    db.refresh(job)

    notification_service.create_notification(
        db=db, user_id=current_user.id, type=NotificationType.JOB_REJECTED,
        title="Job Rejected",
        message=f'You rejected "{job.title}" at {job.company or "Unknown Company"}.',
        job_id=job.id,
    )
    return job
