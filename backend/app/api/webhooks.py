import json
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Header, Query, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.job import Job, JobStatus
from app.models.job_analysis import JobAnalysis
from app.models.notification import NotificationType
from app.models.webhook import WebhookSubscription
from app.schemas.webhook import (
    InboundJobWebhookPayload, InboundJobWebhookResponse,
    WebhookSubscriptionCreate, WebhookSubscriptionUpdate,
    WebhookSubscriptionResponse, WebhookTokenResponse, WebhookTestResponse,
)
from app.api.deps import get_current_user
from app.api.helpers import (
    get_user_profile, get_portfolio_projects,
    serialize_profile, serialize_projects, serialize_analysis_fields,
)
from app.services.duplicate_detection import check_duplicate
from app.services import notification_service
from app.services.webhook_service import (
    generate_or_get_user_token, regenerate_user_token,
    get_user_by_webhook_token, normalize_events, parse_events,
    dispatch_webhook_event, send_test_ping,
)
from app.ai import get_ai_provider
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


# -------------------------------------------------------------------
# INBOUND WEBHOOK (Token Auth)
# -------------------------------------------------------------------

@router.post("/jobs", response_model=InboundJobWebhookResponse, status_code=status.HTTP_200_OK)
async def ingest_job_webhook(
    payload: InboundJobWebhookPayload,
    request: Request,
    x_webhook_token: Optional[str] = Header(None, alias="X-Webhook-Token"),
    token: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Ingest a job opportunity from external automation."""
    auth_token = x_webhook_token or token
    if not auth_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing webhook authentication token.")

    user = get_user_by_webhook_token(db, auth_token)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook token.")

    # Duplicate check
    existing_job = check_duplicate(db, user.id, {
        "title": payload.title, "company": payload.client_name,
        "description": payload.description, "source_job_id": payload.source_job_id,
    })
    if existing_job:
        return InboundJobWebhookResponse(
            success=False, message="Job opportunity already exists (duplicate detected).",
            job_id=existing_job.id, is_duplicate=True,
        )

    raw_meta = {
        "budget": payload.budget, "client_email": payload.client_email,
        "client_linkedin": payload.client_linkedin, "metadata": payload.metadata or {},
    }
    new_job = Job(
        user_id=user.id, title=payload.title,
        company=payload.client_name or "Unknown Client",
        description=payload.description,
        source=payload.source or "n8n_webhook",
        source_job_id=payload.source_job_id,
        raw_content=json.dumps(raw_meta), status=JobStatus.NEW,
    )
    db.add(new_job)
    db.commit()
    db.refresh(new_job)

    notification_service.create_notification(
        db=db, user_id=user.id, type=NotificationType.NEW_JOB,
        title="New Inbound Job Ingested",
        message=f'"{new_job.title}" ingested from {new_job.source}.',
        job_id=new_job.id,
    )

    await dispatch_webhook_event(
        db=db, user_id=user.id, event_type="job.discovered",
        payload={
            "job_id": new_job.id, "title": new_job.title, "company": new_job.company,
            "budget": payload.budget, "source": new_job.source,
            "source_job_id": new_job.source_job_id, "description_snippet": new_job.description[:200],
        },
    )

    # Attempt automatic AI analysis if profile exists
    match_score = None
    profile = get_user_profile(db, user.id, required=False)
    if profile:
        try:
            projects = get_portfolio_projects(db, profile.id)
            ai_provider = get_ai_provider()
            analysis_result = await ai_provider.analyze_opportunity(
                job_description=new_job.description,
                startup_profile=serialize_profile(profile),
                portfolio_projects=serialize_projects(projects),
            )

            analysis_data = serialize_analysis_fields(analysis_result.model_dump())
            analysis = JobAnalysis(job_id=new_job.id, **analysis_data)
            db.add(analysis)

            match_score = analysis.match_score
            if match_score >= settings.MATCH_THRESHOLD:
                new_job.status = JobStatus.REVIEW_REQUIRED
                notification_service.create_notification(
                    db=db, user_id=user.id, type=NotificationType.REVIEW_REQUIRED,
                    title="High Match — Webhook Lead",
                    message=f'"{new_job.title}" scored {match_score}/100. Ready for review.',
                    job_id=new_job.id,
                )
                await dispatch_webhook_event(
                    db=db, user_id=user.id, event_type="job.high_match",
                    payload={
                        "job_id": new_job.id, "title": new_job.title, "company": new_job.company,
                        "match_score": match_score, "key_strengths": analysis_result.key_strengths,
                        "recommendation": analysis_result.recommendation,
                    },
                )
            else:
                new_job.status = JobStatus.REJECTED

            db.commit()
            db.refresh(new_job)
        except Exception as e:
            logger.warning(f"Auto-analysis on webhook ingestion skipped/failed: {e}")

    return InboundJobWebhookResponse(
        success=True, message="Job opportunity successfully ingested and processed.",
        job_id=new_job.id, is_duplicate=False, match_score=match_score,
    )


# -------------------------------------------------------------------
# TOKEN MANAGEMENT (JWT Authenticated)
# -------------------------------------------------------------------

@router.get("/token", response_model=WebhookTokenResponse)
def get_webhook_token(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Retrieve or generate the user's personal inbound webhook token."""
    return WebhookTokenResponse(
        webhook_token=generate_or_get_user_token(current_user, db),
        inbound_url="/api/webhooks/jobs",
    )


@router.post("/token/regenerate", response_model=WebhookTokenResponse)
def regenerate_webhook_token(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Regenerate a fresh inbound webhook token."""
    return WebhookTokenResponse(
        webhook_token=regenerate_user_token(current_user, db),
        inbound_url="/api/webhooks/jobs",
    )


# -------------------------------------------------------------------
# OUTBOUND SUBSCRIPTIONS CRUD (JWT Authenticated)
# -------------------------------------------------------------------

def _sub_response(s: WebhookSubscription) -> WebhookSubscriptionResponse:
    """Build a subscription response from an ORM object."""
    return WebhookSubscriptionResponse(
        id=s.id, user_id=s.user_id, target_url=s.target_url,
        description=s.description, secret_token=s.secret_token,
        events=parse_events(s.events), is_active=s.is_active,
        created_at=s.created_at, last_triggered_at=s.last_triggered_at,
        last_status_code=s.last_status_code,
    )


def _get_subscription(db: Session, subscription_id: int, user_id: int) -> WebhookSubscription:
    sub = db.query(WebhookSubscription).filter(
        WebhookSubscription.id == subscription_id, WebhookSubscription.user_id == user_id,
    ).first()
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Webhook subscription not found")
    return sub


@router.get("/subscriptions", response_model=List[WebhookSubscriptionResponse])
def list_webhook_subscriptions(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """List all outbound webhook subscriptions for the current user."""
    subs = db.query(WebhookSubscription).filter(
        WebhookSubscription.user_id == current_user.id,
    ).order_by(WebhookSubscription.created_at.desc()).all()
    return [_sub_response(s) for s in subs]


@router.post("/subscriptions", response_model=WebhookSubscriptionResponse, status_code=status.HTTP_201_CREATED)
def create_webhook_subscription(
    sub_data: WebhookSubscriptionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Register a new outbound webhook endpoint."""
    new_sub = WebhookSubscription(
        user_id=current_user.id, target_url=sub_data.target_url,
        description=sub_data.description, secret_token=sub_data.secret_token,
        events=normalize_events(sub_data.events), is_active=sub_data.is_active,
    )
    db.add(new_sub)
    db.commit()
    db.refresh(new_sub)
    return _sub_response(new_sub)


@router.put("/subscriptions/{subscription_id}", response_model=WebhookSubscriptionResponse)
def update_webhook_subscription(
    subscription_id: int, sub_data: WebhookSubscriptionUpdate,
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db),
):
    """Update an outbound webhook subscription."""
    sub = _get_subscription(db, subscription_id, current_user.id)

    if sub_data.target_url is not None:
        sub.target_url = sub_data.target_url
    if sub_data.description is not None:
        sub.description = sub_data.description
    if sub_data.secret_token is not None:
        sub.secret_token = sub_data.secret_token
    if sub_data.events is not None:
        sub.events = normalize_events(sub_data.events)
    if sub_data.is_active is not None:
        sub.is_active = sub_data.is_active

    db.commit()
    db.refresh(sub)
    return _sub_response(sub)


@router.delete("/subscriptions/{subscription_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_webhook_subscription(
    subscription_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db),
):
    """Delete an outbound webhook subscription."""
    sub = _get_subscription(db, subscription_id, current_user.id)
    db.delete(sub)
    db.commit()
    return None


@router.post("/subscriptions/{subscription_id}/test", response_model=WebhookTestResponse)
async def test_webhook_subscription(
    subscription_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db),
):
    """Send an immediate test ping event to the subscribed endpoint."""
    sub = _get_subscription(db, subscription_id, current_user.id)
    success, status_code, body = await send_test_ping(db, sub)
    return WebhookTestResponse(
        success=success, status_code=status_code, response_body=body,
        message=f"Test ping dispatched (HTTP {status_code})" if success else f"Test ping failed (HTTP {status_code}): {body}",
    )
