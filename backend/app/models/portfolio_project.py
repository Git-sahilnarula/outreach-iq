from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class PortfolioProject(Base):
    __tablename__ = "portfolio_projects"
    
    id = Column(Integer, primary_key=True, index=True)
    startup_profile_id = Column(Integer, ForeignKey("startup_profiles.id"), nullable=False)
    project_name = Column(String, nullable=False)
    description = Column(Text)
    skills = Column(Text)  # JSON string
    portfolio_url = Column(String)
    case_study = Column(Text)
    technologies = Column(Text)  # JSON string
    results = Column(Text)  # JSON string
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    startup_profile = relationship("StartupProfile", back_populates="portfolio_projects")
