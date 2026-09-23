import hmac
import hashlib
import json
import logging
import secrets
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
import httpx
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from app.models.user import User
from app.models.webhook import WebhookSubscription

logger = logging.getLogger(__name__)

SUPPORTED_EVENTS = [
    "job.discovered",
    "job.high_match",
    "proposal.ready",
    "outreach.sent",
]

def generate_or_get_user_token(user: User, db: Session) -> str:
    """Ensure the user has an inbound webhook token, generating one if missing."""
    if not user.webhook_token:
        user.webhook_token = f"whk_{secrets.token_urlsafe(32)}"
        db.commit()
        db.refresh(user)
    return user.webhook_token

def regenerate_user_token(user: User, db: Session) -> str:
    """Generate a fresh inbound webhook token for the user."""
    user.webhook_token = f"whk_{secrets.token_urlsafe(32)}"
    db.commit()
    db.refresh(user)
    return user.webhook_token

def get_user_by_webhook_token(db: Session, token: str) -> Optional[User]:
    """Look up a user by their unique inbound webhook token."""
    if not token:
        return None
    return db.query(User).filter(User.webhook_token == token).first()

def sign_payload(secret: str, payload_bytes: bytes) -> str:
    """Generate HMAC-SHA256 hex signature for webhook payload."""
    signature = hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()
    return f"sha256={signature}"

def normalize_events(events: Optional[List[str]]) -> str:
    """Normalize event list into comma-separated string."""
    if not events or "*" in events:
        return "*"
    valid = [e.strip() for e in events if e.strip() in SUPPORTED_EVENTS]
    return ",".join(valid) if valid else "*"

def parse_events(events_str: str) -> List[str]:
    """Parse comma-separated string into event list."""
    if not events_str or events_str == "*":
        return ["*"]
    return [e.strip() for e in events_str.split(",") if e.strip()]

async def dispatch_webhook_event(
    db: Session,
    user_id: int,
    event_type: str,
    payload: Dict[str, Any]
) -> int:
    """
    Find all active subscriptions for user matching event_type and dispatch HTTP POST.
    Returns number of subscriptions successfully dispatched.
    """
    subscriptions = db.query(WebhookSubscription).filter(
        WebhookSubscription.user_id == user_id,
        WebhookSubscription.is_active == True
    ).all()

    matching_subs = [
        sub for sub in subscriptions
        if sub.events == "*" or event_type in [e.strip() for e in sub.events.split(",")]
    ]

    if not matching_subs:
        return 0

    envelope = {
        "event": event_type,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "data": payload
    }
    raw_body = json.dumps(envelope, default=str).encode("utf-8")

    success_count = 0
    async with httpx.AsyncClient(timeout=10.0) as client:
        for sub in matching_subs:
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "OutreachIQ-Webhooks/1.0",
                "X-OutreachIQ-Event": event_type,
            }
            if sub.secret_token:
                headers["X-OutreachIQ-Signature"] = sign_payload(sub.secret_token, raw_body)

            try:
                resp = await client.post(sub.target_url, content=raw_body, headers=headers)
                sub.last_triggered_at = func.now()
                sub.last_status_code = resp.status_code
                if resp.status_code < 400:
                    success_count += 1
            except Exception as e:
                logger.warning(f"Failed to deliver webhook {sub.id} to {sub.target_url}: {e}")
                sub.last_triggered_at = func.now()
                sub.last_status_code = 0
            
            db.commit()

    return success_count

async def send_test_ping(db: Session, subscription: WebhookSubscription) -> Tuple[bool, int, str]:
    """Send an immediate test event to a subscription and record results."""
    envelope = {
        "event": "test.ping",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "data": {
            "message": "This is a test notification from Outreach IQ",
            "subscription_id": subscription.id,
            "target_url": subscription.target_url
        }
    }
    raw_body = json.dumps(envelope, default=str).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "OutreachIQ-Webhooks/1.0",
        "X-OutreachIQ-Event": "test.ping",
    }
    if subscription.secret_token:
        headers["X-OutreachIQ-Signature"] = sign_payload(subscription.secret_token, raw_body)

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(subscription.target_url, content=raw_body, headers=headers)
            subscription.last_triggered_at = func.now()
            subscription.last_status_code = resp.status_code
            db.commit()
            return resp.status_code < 400, resp.status_code, resp.text[:500]
    except Exception as e:
        subscription.last_triggered_at = func.now()
        subscription.last_status_code = 0
        db.commit()
        return False, 0, str(e)
