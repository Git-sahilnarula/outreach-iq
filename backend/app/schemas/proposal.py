from pydantic import BaseModel, field_validator, ConfigDict
from datetime import datetime
from typing import Optional, List, Union
import json
from app.models.proposal import ProposalStatus


class ProposalGenerateRequest(BaseModel):
    tone: str = "professional"
    custom_instructions: Optional[str] = None
    include_portfolio_ids: Optional[List[int]] = None


class ProposalUpdateRequest(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    cover_letter: Optional[str] = None
    estimated_duration: Optional[str] = None
    estimated_budget: Optional[str] = None
    tone: Optional[str] = None
    status: Optional[ProposalStatus] = None


class ProposalGenerated(BaseModel):
    title: str
    content: str
    cover_letter: Optional[str] = None
    estimated_duration: Optional[str] = None
    estimated_budget: Optional[str] = None
    relevant_projects: Optional[List[int]] = None


class ProposalResponse(BaseModel):
    id: int
    job_id: int
    user_id: int
    version: int
    title: str
    tone: str
    custom_instructions: Optional[str] = None
    content: str
    cover_letter: Optional[str] = None
    estimated_duration: Optional[str] = None
    estimated_budget: Optional[str] = None
    relevant_projects: Optional[List[int]] = None
    status: ProposalStatus
    created_at: datetime
    updated_at: Optional[datetime] = None

    @field_validator('relevant_projects', mode='before')
    @classmethod
    def parse_json_field(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except Exception:
                return []
        return v

    model_config = ConfigDict(from_attributes=True)
