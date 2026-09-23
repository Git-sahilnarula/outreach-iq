from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Numeric
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class JobAnalysis(Base):
    __tablename__ = "job_analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False, unique=True)
    can_do = Column(String)  # "true" or "false" as string for compatibility
    confidence = Column(Numeric(3, 2))
    match_score = Column(Integer)
    technical_match = Column(Integer)
    service_match = Column(Integer)
    experience_match = Column(Integer)
    budget_match = Column(Integer)
    location_match = Column(Integer)
    reasoning = Column(Text)  # JSON string
    missing_requirements = Column(Text)  # JSON string
    risks = Column(Text)  # JSON string
    recommended_action = Column(String)
    relevant_portfolio_projects = Column(Text)  # JSON string
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    job = relationship("Job", back_populates="analysis")
