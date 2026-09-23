from pydantic import BaseModel, field_validator, ConfigDict
from datetime import datetime
from typing import Optional, List, Union
import json

class PortfolioProjectBase(BaseModel):
    project_name: str
    description: Optional[str] = None
    skills: Optional[Union[List[str], str]] = None
    portfolio_url: Optional[str] = None
    case_study: Optional[str] = None
    technologies: Optional[Union[List[str], str]] = None
    results: Optional[Union[List[str], str]] = None
    
    @field_validator('skills', 'technologies', 'results', mode='before')
    @classmethod
    def parse_json_field(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except:
                return v
        return v

class PortfolioProjectCreate(PortfolioProjectBase):
    pass

class PortfolioProjectUpdate(PortfolioProjectBase):
    pass

class PortfolioProjectResponse(PortfolioProjectBase):
    id: int
    startup_profile_id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
