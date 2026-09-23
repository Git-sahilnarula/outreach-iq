"""
Gmail API endpoints (Phase 2).

Endpoints:
  GET  /api/gmail/auth-url     — Generate OAuth URL for frontend redirect
  GET  /api/gmail/callback     — OAuth callback from Google
  GET  /api/gmail/status       — Connection status + last sync time
  POST /api/gmail/sync         — Manually trigger an email sync
  DELETE /api/gmail/disconnect — Revoke stored tokens
"""
import json
import logging
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.job import Job, JobStatus
from app.schemas.gmail import GmailStatusResponse, GmailSyncResponse, GmailAuthUrlResponse
from app.services.duplicate_detection import check_duplicate
from app.services import notification_service
from app.models.notification import NotificationType
from app.config import settings
from app.integrations import gmail_client, email_parser

logger = logging.getLogger(__name__)

router = APIRouter()


def _gmail_configured() -> bool:
    """Check if Google OAuth credentials are set in config."""
    return bool(settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET)


# ---------------------------------------------------------------------------
# GET /api/gmail/auth-url
# ---------------------------------------------------------------------------
@router.get("/auth-url", response_model=GmailAuthUrlResponse)
def get_auth_url(
    current_user: User = Depends(get_current_user),
):
    """
    Generate the Google OAuth 2.0 URL.
    The frontend redirects the user to this URL to grant Gmail access.
    """
    if not _gmail_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Gmail integration is not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env.",
        )

    # Use user_id as the OAuth state for CSRF protection
    auth_url = gmail_client.get_auth_url(state=str(current_user.id))
    return GmailAuthUrlResponse(auth_url=auth_url)


# ---------------------------------------------------------------------------
# GET /api/gmail/callback
# ---------------------------------------------------------------------------
@router.get("/callback")
def oauth_callback(
    code: str = Query(..., description="Authorization code from Google"),
    state: str = Query(..., description="User ID passed as OAuth state"),
    error: str = Query(None, description="Error from Google if user denied access"),
    db: Session = Depends(get_db),
):
    """
    OAuth 2.0 callback endpoint.
    Google redirects here after the user grants/denies access.
    Exchanges the code for tokens, saves them, then redirects to frontend.
    """
    # Determine frontend URL
    frontend_url = "http://localhost:5173"

    if error:
        logger.warning(f"OAuth denied for state={state}: {error}")
        return RedirectResponse(url=f"{frontend_url}/gmail?error=access_denied")

    if not _gmail_configured():
        return RedirectResponse(url=f"{frontend_url}/gmail?error=not_configured")

    try:
        user_id = int(state)
    except ValueError:
        return RedirectResponse(url=f"{frontend_url}/gmail?error=invalid_state")

    try:
        gmail_client.exchange_code_and_save(db=db, user_id=user_id, code=code)
        logger.info(f"Gmail connected for user {user_id}")
        return RedirectResponse(url=f"{frontend_url}/gmail?connected=true")
    except Exception as e:
        logger.error(f"OAuth callback failed for user {user_id}: {e}")
        return RedirectResponse(url=f"{frontend_url}/gmail?error=token_exchange_failed")


# ---------------------------------------------------------------------------
# GET /api/gmail/status
# ---------------------------------------------------------------------------
@router.get("/status", response_model=GmailStatusResponse)
def get_gmail_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return whether Gmail is connected and when it was last synced."""
    token_record = gmail_client.get_token_record(db, current_user.id)

    if not token_record:
        return GmailStatusResponse(connected=False)

    return GmailStatusResponse(
        connected=True,
        gmail_email=token_record.gmail_email,
        last_sync_at=token_record.last_sync_at,
    )


# ---------------------------------------------------------------------------
# POST /api/gmail/sync
# ---------------------------------------------------------------------------
@router.post("/sync", response_model=GmailSyncResponse)
async def sync_gmail(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Manually trigger a Gmail sync.

    Fetches emails from the configured Job Alerts label, parses each with AI,
    and inserts new jobs into the database (skipping duplicates).
    """
    if not _gmail_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Gmail integration is not configured.",
        )

    if not gmail_client.is_connected(db, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Gmail is not connected. Please connect your Gmail account first.",
        )

    # Fetch emails
    try:
        emails = gmail_client.fetch_job_alert_emails(
            db=db,
            user_id=current_user.id,
            max_results=settings.GMAIL_MAX_EMAILS_PER_SYNC,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to fetch Gmail emails for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to fetch emails from Gmail: {str(e)}",
        )

    counters = {
        "new_jobs": 0,
        "duplicates_skipped": 0,
        "not_job_emails": 0,
        "errors": 0,
    }
    processed_ids = []

    for email in emails:
        try:
            # Parse email into a JobCreate
            job_create = await email_parser.parse_job_from_email(
                subject=email["subject"],
                sender=email["sender"],
                body=email["body_text"],
                message_id=email["id"],
            )

            if job_create is None:
                counters["not_job_emails"] += 1
                # Still mark as processed so we don't re-check it
                processed_ids.append(email["id"])
                continue

            # Duplicate check
            job_data = job_create.model_dump()
            if job_data.get("skills") and isinstance(job_data["skills"], list):
                job_data["skills"] = json.dumps(job_data["skills"])

            existing = check_duplicate(db, current_user.id, job_create.model_dump())
            if existing:
                counters["duplicates_skipped"] += 1
                processed_ids.append(email["id"])
                continue

            # Save to DB
            skills_value = job_data.get("skills")
            if isinstance(skills_value, list):
                skills_value = json.dumps(skills_value)

            new_job = Job(
                user_id=current_user.id,
                source="gmail",
                source_job_id=job_create.source_job_id,
                title=job_create.title,
                company=job_create.company,
                description=job_create.description,
                url=job_create.url,
                location=job_create.location,
                job_type=job_create.job_type,
                salary_min=job_create.salary_min,
                salary_max=job_create.salary_max,
                currency=job_create.currency or "USD",
                skills=skills_value,
                raw_content=getattr(job_create, "raw_content", None),
                status=JobStatus.NEW,
            )
            db.add(new_job)
            db.commit()

            counters["new_jobs"] += 1
            processed_ids.append(email["id"])

        except Exception as e:
            logger.error(f"Failed to process email {email.get('id')}: {e}")
            counters["errors"] += 1

    # Mark processed emails in Gmail so they won't be re-ingested
    if processed_ids:
        try:
            gmail_client.mark_as_processed(db, current_user.id, processed_ids)
        except Exception as e:
            logger.warning(f"Failed to mark emails as processed: {e}")

    # Update last_sync_at
    gmail_client.update_last_sync(db, current_user.id)

    total = len(emails)
    new = counters["new_jobs"]
    msg = (
        f"Sync complete. {new} new job{'s' if new != 1 else ''} added from {total} email{'s' if total != 1 else ''}."
        if total > 0
        else "No new job-alert emails found. Make sure emails are labelled \"Job Alerts\" in Gmail."
    )

    # Phase 3: create a summary notification if any new jobs were found
    if new > 0:
        notification_service.create_notification(
            db=db,
            user_id=current_user.id,
            type=NotificationType.NEW_JOB,
            title="Gmail Sync Complete",
            message=f"{new} new job opportunit{'ies' if new != 1 else 'y'} ingested from Gmail.",
        )

    return GmailSyncResponse(
        new_jobs=counters["new_jobs"],
        duplicates_skipped=counters["duplicates_skipped"],
        not_job_emails=counters["not_job_emails"],
        errors=counters["errors"],
        total_processed=total,
        message=msg,
    )


# ---------------------------------------------------------------------------
# DELETE /api/gmail/disconnect
# ---------------------------------------------------------------------------
@router.delete("/disconnect")
def disconnect_gmail(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Remove stored Gmail tokens, disconnecting the account."""
    removed = gmail_client.disconnect(db, current_user.id)
    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No Gmail connection found.",
        )
    return {"message": "Gmail disconnected successfully."}
