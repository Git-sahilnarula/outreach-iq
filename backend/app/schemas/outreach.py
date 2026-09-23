from pydantic import BaseModel, ConfigDict, EmailStr
from datetime import datetime
from typing import Optional
from app.models.outreach import OutreachStatus


class OutreachDraftCreate(BaseModel):
    recipient_email: str
    recipient_name: Optional[str] = None
    subject: str
    body: str
    proposal_id: Optional[int] = None


class OutreachUpdate(BaseModel):
    recipient_email: Optional[str] = None
    recipient_name: Optional[str] = None
    subject: Optional[str] = None
    body: Optional[str] = None


class OutreachSendRequest(BaseModel):
    recipient_email: str
    recipient_name: Optional[str] = None
    subject: str
    body: str
    proposal_id: Optional[int] = None
    confirm_send: bool = True


class OutreachResponse(BaseModel):
    id: int
    job_id: int
    user_id: int
    proposal_id: Optional[int] = None
    recipient_email: str
    recipient_name: Optional[str] = None
    subject: str
    body: str
    status: OutreachStatus
    gmail_message_id: Optional[str] = None
    gmail_thread_id: Optional[str] = None
    sent_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
