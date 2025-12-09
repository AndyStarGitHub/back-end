from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.models.notification import NotificationStatusEnum


class NotificationRead(BaseModel):
    id: UUID
    user_id: int

    company_id: UUID | None = None
    quiz_id: UUID | None = None

    message: str
    status: NotificationStatusEnum
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    total: int
    items: list[NotificationRead]
    offset: int
    limit: int
