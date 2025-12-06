from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFound, Forbidden
from app.repositories.notification import NotificationRepository
from app.schemas.notification import (
    NotificationRead,
    NotificationListResponse,
)
from app.models.notification import NotificationStatusEnum


class NotificationService:
    def __init__(
        self,
        notification_repo: NotificationRepository | None = None,
    ) -> None:
        self.notification_repo = notification_repo or NotificationRepository()

    async def list_my_notifications(
        self,
        db: AsyncSession,
        *,
        current_user: Any,
        offset: int = 0,
        limit: int = 50,
    ) -> NotificationListResponse:

        total, items = await self.notification_repo.get_paginated_for_user(
            db,
            user_id=current_user.id,
            offset=offset,
            limit=limit,
        )

        return NotificationListResponse(
            total=total,
            items=[NotificationRead.model_validate(n) for n in items],
            offset=offset,
            limit=limit,
        )

    async def mark_notification_as_read(
        self,
        db: AsyncSession,
        *,
        notification_id: UUID,
        current_user: Any,
    ) -> NotificationRead:

        notification = await self.notification_repo.get_by_id(
            db,
            notification_id,
        )

        if notification is None:
            raise NotFound("Notification not found")

        if notification.user_id != current_user.id:
            raise Forbidden("You can only modify your own notifications")

        updated = await self.notification_repo.update_one(
            db,
            obj_id=notification_id,
            status=NotificationStatusEnum.READ,
        )

        return NotificationRead.model_validate(updated)
