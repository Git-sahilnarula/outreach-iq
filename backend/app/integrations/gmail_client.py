"""
Gmail OAuth 2.0 client.

Handles the full OAuth flow, fetching emails, and decoding their content.
Uses google-api-python-client under the hood.
"""
import base64
import json
import logging
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional, List, Dict, Any

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from sqlalchemy.orm import Session

from app.config import settings
from app.models.gmail_token import GmailToken

logger = logging.getLogger(__name__)

# Scopes required — read-only + labels + sending
GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.labels",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/userinfo.email",
    "openid",
]


# Label we add to processed emails to avoid re-ingestion
PROCESSED_LABEL_NAME = "OutreachIQ/Processed"


def _build_client_config() -> dict:
    """Build the OAuth client config dict from settings."""
    return {
        "web": {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uris": [settings.GOOGLE_REDIRECT_URI],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    }


def get_auth_url(state: str) -> str:
    """
    Generate the Google OAuth 2.0 authorization URL.
    
    Args:
        state: An opaque string (e.g. user_id) passed through OAuth for CSRF protection.
    
    Returns:
        The URL to redirect the user to for Google consent.
    """
    flow = Flow.from_client_config(
        _build_client_config(),
        scopes=GMAIL_SCOPES,
        redirect_uri=settings.GOOGLE_REDIRECT_URI,
    )
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",  # Force refresh_token every time
        state=state,
    )
    return auth_url


def exchange_code_and_save(db: Session, user_id: int, code: str) -> GmailToken:
    """
    Exchange an OAuth authorization code for tokens and persist them.
    
    Args:
        db: Database session.
        user_id: The authenticated user's ID.
        code: The authorization code from the OAuth callback.
    
    Returns:
        The saved GmailToken record.
    """
    flow = Flow.from_client_config(
        _build_client_config(),
        scopes=GMAIL_SCOPES,
        redirect_uri=settings.GOOGLE_REDIRECT_URI,
    )
    flow.fetch_token(code=code)
    creds = flow.credentials

    # Fetch the user's Gmail address
    gmail_email = _get_gmail_email(creds)

    # Upsert token record
    token_record = db.query(GmailToken).filter(GmailToken.user_id == user_id).first()
    if token_record:
        token_record.access_token = creds.token
        token_record.refresh_token = creds.refresh_token or token_record.refresh_token
        token_record.token_expiry = creds.expiry
        token_record.gmail_email = gmail_email
    else:
        token_record = GmailToken(
            user_id=user_id,
            access_token=creds.token,
            refresh_token=creds.refresh_token,
            token_expiry=creds.expiry,
            gmail_email=gmail_email,
        )
        db.add(token_record)

    db.commit()
    db.refresh(token_record)
    return token_record


def _get_gmail_email(creds: Credentials) -> Optional[str]:
    """Fetch the email address associated with these credentials."""
    try:
        service = build("oauth2", "v2", credentials=creds)
        info = service.userinfo().get().execute()
        return info.get("email")
    except Exception as e:
        logger.warning(f"Could not fetch Gmail email: {e}")
        return None


def _load_credentials(db: Session, user_id: int) -> Optional[Credentials]:
    """
    Load and auto-refresh credentials from the database.
    
    Returns None if no token exists.
    """
    token_record = db.query(GmailToken).filter(GmailToken.user_id == user_id).first()
    if not token_record:
        return None

    creds = Credentials(
        token=token_record.access_token,
        refresh_token=token_record.refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        scopes=GMAIL_SCOPES,
    )

    # Refresh if expired
    if creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            # Persist updated token
            token_record.access_token = creds.token
            token_record.token_expiry = creds.expiry
            db.commit()
        except Exception as e:
            logger.error(f"Failed to refresh Gmail token for user {user_id}: {e}")
            return None

    return creds


def is_connected(db: Session, user_id: int) -> bool:
    """Check if the user has a connected Gmail account."""
    token_record = db.query(GmailToken).filter(GmailToken.user_id == user_id).first()
    return token_record is not None and token_record.refresh_token is not None


def get_token_record(db: Session, user_id: int) -> Optional[GmailToken]:
    """Return the raw GmailToken record for a user."""
    return db.query(GmailToken).filter(GmailToken.user_id == user_id).first()


def disconnect(db: Session, user_id: int) -> bool:
    """
    Remove the stored Gmail tokens for a user.
    
    Returns True if a record was found and deleted.
    """
    token_record = db.query(GmailToken).filter(GmailToken.user_id == user_id).first()
    if token_record:
        db.delete(token_record)
        db.commit()
        return True
    return False


def _get_or_create_label(service, label_name: str) -> Optional[str]:
    """Return the ID of a Gmail label, creating it if it doesn't exist."""
    try:
        result = service.users().labels().list(userId="me").execute()
        for label in result.get("labels", []):
            if label["name"] == label_name:
                return label["id"]
        # Create it
        created = service.users().labels().create(
            userId="me",
            body={
                "name": label_name,
                "labelListVisibility": "labelShow",
                "messageListVisibility": "show",
            },
        ).execute()
        return created["id"]
    except HttpError as e:
        logger.warning(f"Could not get/create label '{label_name}': {e}")
        return None


def fetch_job_alert_emails(
    db: Session,
    user_id: int,
    max_results: int = 50,
) -> List[Dict[str, Any]]:
    """
    Fetch unprocessed emails from the configured Job Alerts label.

    Returns a list of dicts with keys:
        id, thread_id, subject, sender, date, body_text, snippet
    """
    creds = _load_credentials(db, user_id)
    if not creds:
        raise ValueError("No valid Gmail credentials found. Please reconnect Gmail.")

    service = build("gmail", "v1", credentials=creds)

    # Build query: label is "Job Alerts" AND NOT labelled as processed
    label_filter = f'label:"{settings.GMAIL_JOB_ALERT_LABEL}"'
    processed_filter = f'-label:"{PROCESSED_LABEL_NAME}"'
    query = f"{label_filter} {processed_filter}"

    try:
        response = service.users().messages().list(
            userId="me",
            q=query,
            maxResults=max_results,
        ).execute()
    except HttpError as e:
        logger.error(f"Gmail API error listing messages: {e}")
        raise ValueError(f"Gmail API error: {e}")

    messages = response.get("messages", [])
    results = []

    for msg_meta in messages:
        msg_id = msg_meta["id"]
        try:
            email_data = _parse_message(service, msg_id)
            if email_data:
                results.append(email_data)
        except Exception as e:
            logger.warning(f"Failed to parse message {msg_id}: {e}")
            continue

    return results


def _parse_message(service, msg_id: str) -> Optional[Dict[str, Any]]:
    """Fetch and decode a single Gmail message."""
    msg = service.users().messages().get(
        userId="me",
        id=msg_id,
        format="full",
    ).execute()

    headers = {h["name"].lower(): h["value"] for h in msg.get("payload", {}).get("headers", [])}
    subject = headers.get("subject", "(No Subject)")
    sender = headers.get("from", "")
    date_str = headers.get("date", "")
    snippet = msg.get("snippet", "")

    body_text = _extract_body(msg.get("payload", {}))

    return {
        "id": msg_id,
        "thread_id": msg.get("threadId"),
        "subject": subject,
        "sender": sender,
        "date": date_str,
        "body_text": body_text,
        "snippet": snippet,
    }


def _extract_body(payload: dict) -> str:
    """
    Recursively extract plain text or HTML body from Gmail message payload.
    Prefers text/plain; falls back to text/html.
    """
    mime_type = payload.get("mimeType", "")
    body_data = payload.get("body", {}).get("data")

    if body_data:
        decoded = base64.urlsafe_b64decode(body_data + "==").decode("utf-8", errors="replace")
        if mime_type == "text/plain":
            return decoded
        if mime_type == "text/html":
            return decoded  # Caller will strip HTML

    # Recurse into parts
    plain_parts = []
    html_parts = []
    for part in payload.get("parts", []):
        part_mime = part.get("mimeType", "")
        part_data = part.get("body", {}).get("data")
        if part_data:
            decoded = base64.urlsafe_b64decode(part_data + "==").decode("utf-8", errors="replace")
            if part_mime == "text/plain":
                plain_parts.append(decoded)
            elif part_mime == "text/html":
                html_parts.append(decoded)
        # Recurse multipart
        if part.get("parts"):
            sub_text = _extract_body(part)
            if sub_text:
                plain_parts.append(sub_text)

    if plain_parts:
        return "\n".join(plain_parts)
    if html_parts:
        return "\n".join(html_parts)
    return ""


def mark_as_processed(db: Session, user_id: int, message_ids: List[str]) -> None:
    """
    Add the 'OutreachIQ/Processed' label to a list of messages so they
    are not ingested again on the next sync.
    """
    if not message_ids:
        return

    creds = _load_credentials(db, user_id)
    if not creds:
        return

    service = build("gmail", "v1", credentials=creds)
    label_id = _get_or_create_label(service, PROCESSED_LABEL_NAME)
    if not label_id:
        return

    try:
        service.users().messages().batchModify(
            userId="me",
            body={
                "ids": message_ids,
                "addLabelIds": [label_id],
            },
        ).execute()
    except HttpError as e:
        logger.warning(f"Failed to mark messages as processed: {e}")


def update_last_sync(db: Session, user_id: int) -> None:
    """Update the last_sync_at timestamp for a user."""
    token_record = db.query(GmailToken).filter(GmailToken.user_id == user_id).first()
    if token_record:
        token_record.last_sync_at = datetime.now(timezone.utc)
        db.commit()


def send_email(
    db: Session,
    user_id: int,
    to_email: str,
    subject: str,
    body_text: str,
    body_html: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Send an email via the user's connected Gmail account.

    Args:
        db: Database session.
        user_id: Current user ID.
        to_email: Destination recipient email.
        subject: Email subject.
        body_text: Plain-text email body.
        body_html: Optional HTML version.

    Returns:
        dict: {"id": message_id, "threadId": thread_id}
    """
    creds = _load_credentials(db, user_id)
    if not creds:
        raise ValueError("Gmail account is not connected for this user. Connect Gmail in settings first.")

    service = build("gmail", "v1", credentials=creds)

    message = MIMEMultipart("alternative")
    message["to"] = to_email
    message["subject"] = subject

    part_text = MIMEText(body_text, "plain", "utf-8")
    message.attach(part_text)

    if body_html:
        part_html = MIMEText(body_html, "html", "utf-8")
        message.attach(part_html)

    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")

    try:
        sent_msg = service.users().messages().send(
            userId="me",
            body={"raw": raw_message}
        ).execute()

        logger.info(f"Outreach email dispatched to {to_email} (message_id={sent_msg.get('id')})")
        return {
            "id": sent_msg.get("id"),
            "threadId": sent_msg.get("threadId"),
        }
    except HttpError as e:
        logger.error(f"Gmail API send failed: {e}")
        raise

