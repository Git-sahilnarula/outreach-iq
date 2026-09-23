from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class GmailStatusResponse(BaseModel):
    """Response for GET /api/gmail/status"""
    connected: bool
    gmail_email: Optional[str] = None
    last_sync_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class GmailSyncResponse(BaseModel):
    """Response for POST /api/gmail/sync"""
    new_jobs: int
    duplicates_skipped: int
    not_job_emails: int
    errors: int
    total_processed: int
    message: str


class GmailAuthUrlResponse(BaseModel):
    """Response for GET /api/gmail/auth-url"""
    auth_url: str
