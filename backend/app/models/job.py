from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Numeric, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import enum

class JobStatus(str, enum.Enum):
    NEW = "NEW"
    ANALYZING = "ANALYZING"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    REJECTED = "REJECTED"
    APPROVED = "APPROVED"
    PROPOSAL_PENDING = "PROPOSAL_PENDING"
    PROPOSAL_READY = "PROPOSAL_READY"
    PROPOSAL_APPROVED = "PROPOSAL_APPROVED"
    OUTREACH_PENDING = "OUTREACH_PENDING"
    CONTACTED = "CONTACTED"
    CLOSED = "CLOSED"

class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    source = Column(String, nullable=False, default="manual")
    source_job_id = Column(String, index=True)
    url = Column(String)
    title = Column(String, nullable=False)
    company = Column(String)
    description = Column(Text, nullable=False)
    location = Column(String)
    job_type = Column(String)
    salary_min = Column(Numeric(10, 2))
    salary_max = Column(Numeric(10, 2))
    currency = Column(String, default="USD")
    skills = Column(Text)  # JSON string
    posted_at = Column(DateTime(timezone=True))
    discovered_at = Column(DateTime(timezone=True), server_default=func.now())
    raw_content = Column(Text)
    status = Column(SQLEnum(JobStatus), default=JobStatus.NEW, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    user = relationship("User")
    analysis = relationship("JobAnalysis", back_populates="job", uselist=False, cascade="all, delete-orphan")
    proposals = relationship("Proposal", back_populates="job", cascade="all, delete-orphan", order_by="desc(Proposal.version)")
    outreach_messages = relationship("OutreachMessage", back_populates="job", cascade="all, delete-orphan", order_by="desc(OutreachMessage.created_at)")
    linkedin_messages = relationship("LinkedInMessage", back_populates="job", cascade="all, delete-orphan", order_by="desc(LinkedInMessage.created_at)")


