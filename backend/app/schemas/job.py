from pydantic import BaseModel, field_validator, ConfigDict
from datetime import datetime
from typing import Optional, List, Union
from decimal import Decimal
from app.models.job import JobStatus
import json

class JobBase(BaseModel):
    source: str = "manual"
    source_job_id: Optional[str] = None
    url: Optional[str] = None
    title: str
    company: Optional[str] = None
    description: str
    location: Optional[str] = None
    job_type: Optional[str] = None
    salary_min: Optional[Decimal] = None
    salary_max: Optional[Decimal] = None
    currency: str = "USD"
    skills: Optional[Union[List[str], str]] = None
    posted_at: Optional[datetime] = None
    
    @field_validator('skills', mode='before')
    @classmethod
    def parse_json_field(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except:
                return v
        return v

class JobCreate(JobBase):
    pass

class JobUpdate(JobBase):
    pass

class JobResponse(JobBase):
    id: int
    user_id: int
    discovered_at: datetime
    raw_content: Optional[str] = None
    status: JobStatus
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
