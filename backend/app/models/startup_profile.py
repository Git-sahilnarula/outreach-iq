from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Numeric
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class StartupProfile(Base):
    __tablename__ = "startup_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    startup_name = Column(String, nullable=False)
    description = Column(Text)
    website = Column(String)
    industry = Column(String)
    services = Column(Text)  # JSON string
    technical_skills = Column(Text)  # JSON string
    preferred_job_types = Column(Text)  # JSON string
    preferred_industries = Column(Text)  # JSON string
    minimum_budget = Column(Numeric(10, 2))
    preferred_budget = Column(Numeric(10, 2))
    preferred_locations = Column(Text)  # JSON string
    remote_allowed = Column(Boolean, default=True)
    team_size = Column(Integer)
    certifications = Column(Text)  # JSON string
    keywords = Column(Text)  # JSON string
    excluded_keywords = Column(Text)  # JSON string
    contact_email = Column(String)
    linkedin_url = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    user = relationship("User", back_populates="startup_profile")
    portfolio_projects = relationship("PortfolioProject", back_populates="startup_profile", cascade="all, delete-orphan")
