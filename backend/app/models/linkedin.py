from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class LinkedInMessage(Base):
    __tablename__ = "linkedin_messages"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    recipient_name = Column(String, nullable=True)
    recipient_role = Column(String, nullable=True)
    recipient_profile_url = Column(String, nullable=True)
    tone = Column(String, default="value_first", nullable=False)

    connection_note = Column(String(300), nullable=False)
    inmail_subject = Column(String(200), nullable=False)
    inmail_body = Column(Text, nullable=False)

    status = Column(String, default="GENERATED", nullable=False)  # "GENERATED", "SENT"
    sent_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    job = relationship("Job", back_populates="linkedin_messages")
    user = relationship("User")
