from __future__ import annotations

from uuid import UUID

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from typing import Iterable
from app.models.notification import NotificationStatusEnum

from app.models.notification import Notification
from app.repositories.base import BaseRepository


class NotificationRepository(BaseRepository[Notification]):
    def __init__(self) -> None:
        super().__init__(Notification)

    async def get_paginated_for_user(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[int, list[Notification]]:

        total_result = await db.execute(
            select(func.count()).select_from(Notification).where(
                Notification.user_id == user_id,
            )
        )
        total = total_result.scalar_one()

        result = await db.execute(
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(desc(Notification.created_at))
            .offset(offset)
            .limit(limit)
        )

        items = list(result.scalars().all())
        return total, items

    async def create_many_for_users(
            self,
            db: AsyncSession,
            *,
            user_ids: Iterable[int],
            company_id: UUID | None,
            quiz_id: UUID | None,
            message: str,
            status: NotificationStatusEnum = NotificationStatusEnum.UNREAD,
    ) -> None:

        user_ids_set = {uid for uid in user_ids}
        if not user_ids_set:
            return

        notifications = [
            Notification(
                user_id=uid,
                company_id=company_id,
                quiz_id=quiz_id,
                message=message,
                status=status,
            )
            for uid in user_ids_set
        ]

        db.add_all(notifications)
        await db.commit()
