from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.core.deps import get_current_user
from app.services.notification import NotificationService
from app.schemas.notification import (
    NotificationListResponse,
    NotificationRead,
)


router = APIRouter()

notification_service = NotificationService()


@router.get(
    "/",
    response_model=NotificationListResponse,
)
async def list_my_notifications(
    offset: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):

    return await notification_service.list_my_notifications(
        db,
        current_user=current_user,
        offset=offset,
        limit=limit,
    )


@router.patch(
    "/{notification_id}/read",
    response_model=NotificationRead,
)
async def mark_notification_as_read(
    notification_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):

    return await notification_service.mark_notification_as_read(
        db,
        notification_id=notification_id,
        current_user=current_user,
    )
