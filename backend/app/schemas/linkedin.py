from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class LinkedInGenerateRequest(BaseModel):
    recipient_name: Optional[str] = Field(None, description="Name of the target person (e.g., Hiring Lead / CTO)")
    recipient_role: Optional[str] = Field(None, description="Role/Title of target person (e.g., Engineering Manager)")
    recipient_profile_url: Optional[str] = Field(None, description="LinkedIn profile URL")
    tone: str = Field("value_first", description="Tone: value_first, direct, networking, thought_leadership")
    custom_instructions: Optional[str] = Field(None, description="Custom angles or notes to include")


class LinkedInUpdateRequest(BaseModel):
    recipient_name: Optional[str] = None
    recipient_role: Optional[str] = None
    recipient_profile_url: Optional[str] = None
    connection_note: Optional[str] = Field(None, max_length=300, description="Connection note (max 300 chars)")
    inmail_subject: Optional[str] = None
    inmail_body: Optional[str] = None


class LinkedInMessageResponse(BaseModel):
    id: int
    job_id: int
    user_id: int
    recipient_name: Optional[str] = None
    recipient_role: Optional[str] = None
    recipient_profile_url: Optional[str] = None
    tone: str
    connection_note: str
    inmail_subject: str
    inmail_body: str
    status: str
    sent_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
