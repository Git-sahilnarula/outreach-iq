import enum
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class ProposalStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class Proposal(Base):
    __tablename__ = "proposals"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    version = Column(Integer, default=1, nullable=False)
    title = Column(String, nullable=False)
    tone = Column(String, default="professional", nullable=False)
    custom_instructions = Column(Text, nullable=True)
    content = Column(Text, nullable=False)  # Full markdown proposal
    cover_letter = Column(Text, nullable=True)  # Concise cover letter / pitch version
    estimated_duration = Column(String, nullable=True)
    estimated_budget = Column(String, nullable=True)
    relevant_projects = Column(Text, nullable=True)  # JSON string of referenced project IDs
    status = Column(SQLEnum(ProposalStatus), default=ProposalStatus.DRAFT, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    job = relationship("Job", back_populates="proposals")
    user = relationship("User")
