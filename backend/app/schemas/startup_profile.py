from pydantic import BaseModel, field_validator, ConfigDict
from datetime import datetime
from typing import Optional, List, Union
from decimal import Decimal
import json

class StartupProfileBase(BaseModel):
    startup_name: str
    description: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[str] = None
    services: Optional[Union[List[str], str]] = None
    technical_skills: Optional[Union[List[str], str]] = None
    preferred_job_types: Optional[Union[List[str], str]] = None
    preferred_industries: Optional[Union[List[str], str]] = None
    minimum_budget: Optional[Decimal] = None
    preferred_budget: Optional[Decimal] = None
    preferred_locations: Optional[Union[List[str], str]] = None
    remote_allowed: bool = True
    team_size: Optional[int] = None
    certifications: Optional[Union[List[str], str]] = None
    keywords: Optional[Union[List[str], str]] = None
    excluded_keywords: Optional[Union[List[str], str]] = None
    contact_email: Optional[str] = None
    linkedin_url: Optional[str] = None
    
    @field_validator('services', 'technical_skills', 'preferred_job_types', 'preferred_industries', 'preferred_locations', 'certifications', 'keywords', 'excluded_keywords', mode='before')
    @classmethod
    def parse_json_field(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except:
                return v
        return v

class StartupProfileCreate(StartupProfileBase):
    pass

class StartupProfileUpdate(StartupProfileBase):
    pass

class StartupProfileResponse(StartupProfileBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
