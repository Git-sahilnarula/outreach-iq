from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class GmailToken(Base):
    """Stores Gmail OAuth 2.0 tokens for a user. One row per user."""
    __tablename__ = "gmail_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)

    # Connected Gmail address
    gmail_email = Column(String, nullable=True)

    # OAuth tokens (stored as encrypted-at-rest strings in future; plain for MVP)
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text, nullable=True)
    token_expiry = Column(DateTime(timezone=True), nullable=True)

    # Tracking
    last_sync_at = Column(DateTime(timezone=True), nullable=True)
    last_history_id = Column(String, nullable=True)  # Gmail history ID for incremental sync

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User")
