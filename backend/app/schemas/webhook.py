from pydantic import BaseModel, HttpUrl, Field, ConfigDict
from typing import Optional, List, Dict, Any, Union
from datetime import datetime

class InboundJobWebhookPayload(BaseModel):
    title: str = Field(..., description="Job title / posting headline")
    description: str = Field(..., description="Full job description or summary")
    client_name: Optional[str] = Field(None, description="Client or company name")
    client_email: Optional[str] = Field(None, description="Contact email if available")
    client_linkedin: Optional[str] = Field(None, description="LinkedIn profile or company URL")
    budget: Optional[str] = Field(None, description="Budget or hourly rate string")
    source: Optional[str] = Field("n8n_webhook", description="Origin source e.g. upwork, rss, linkedin")
    source_job_id: Optional[str] = Field(None, description="External job identifier from platform")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Custom metadata/tags")

class InboundJobWebhookResponse(BaseModel):
    success: bool
    message: str
    job_id: Optional[int] = None
    is_duplicate: bool = False
    match_score: Optional[float] = None

class WebhookSubscriptionCreate(BaseModel):
    target_url: str = Field(..., description="Target HTTP/HTTPS webhook URL")
    description: Optional[str] = Field(None, description="Short human-readable label")
    secret_token: Optional[str] = Field(None, description="Optional secret for HMAC-SHA256 signature verification")
    events: Optional[List[str]] = Field(default=["*"], description="List of events e.g. ['job.discovered', 'job.high_match']")
    is_active: bool = True

class WebhookSubscriptionUpdate(BaseModel):
    target_url: Optional[str] = None
    description: Optional[str] = None
    secret_token: Optional[str] = None
    events: Optional[List[str]] = None
    is_active: Optional[bool] = None

class WebhookSubscriptionResponse(BaseModel):
    id: int
    user_id: int
    target_url: str
    description: Optional[str] = None
    secret_token: Optional[str] = None
    events: List[str]
    is_active: bool
    created_at: Optional[datetime] = None
    last_triggered_at: Optional[datetime] = None
    last_status_code: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)

class WebhookTokenResponse(BaseModel):
    webhook_token: str
    inbound_url: str

class WebhookTestResponse(BaseModel):
    success: bool
    status_code: Optional[int] = None
    response_body: Optional[str] = None
    message: str
