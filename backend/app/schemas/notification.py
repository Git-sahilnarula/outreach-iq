from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime


class NotificationResponse(BaseModel):
    id: int
    user_id: int
    type: str
    title: str
    message: str
    job_id: Optional[int] = None
    read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationCountResponse(BaseModel):
    unread: int


class NotificationListResponse(BaseModel):
    notifications: List[NotificationResponse]
    unread: int
