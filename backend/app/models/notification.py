import enum
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class NotificationType(str, enum.Enum):
    NEW_JOB = "NEW_JOB"
    ANALYSIS_COMPLETE = "ANALYSIS_COMPLETE"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    JOB_APPROVED = "JOB_APPROVED"
    JOB_REJECTED = "JOB_REJECTED"
    PROPOSAL_READY = "PROPOSAL_READY"
    PROPOSAL_APPROVED = "PROPOSAL_APPROVED"
    OUTREACH_SENT = "OUTREACH_SENT"




class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    type = Column(String, nullable=False)          # NotificationType value
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="SET NULL"), nullable=True)
    read = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")
    job = relationship("Job")
