from pydantic import BaseModel, field_validator, ConfigDict
from datetime import datetime
from typing import Optional, List, Union
from decimal import Decimal
import json

class JobAnalysisBase(BaseModel):
    can_do: bool
    confidence: Optional[Decimal] = None
    match_score: int
    technical_match: int
    service_match: int
    experience_match: int
    budget_match: int
    location_match: int
    reasoning: Optional[List[str]] = None
    missing_requirements: Optional[List[str]] = None
    risks: Optional[List[str]] = None
    recommended_action: str
    relevant_portfolio_projects: Optional[List[int]] = None
    
    @field_validator('reasoning', 'missing_requirements', 'risks', 'relevant_portfolio_projects', mode='before')
    @classmethod
    def parse_json_field(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except:
                return v
        return v

class JobAnalysisCreate(JobAnalysisBase):
    pass

class JobAnalysisResponse(JobAnalysisBase):
    id: int
    job_id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
