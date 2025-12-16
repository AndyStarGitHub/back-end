import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFound
from app.services.notification import NotificationService

notification_service = NotificationService()


@pytest.mark.asyncio
async def test_mark_notification_as_read_not_found(
    db_session: AsyncSession,
    user_factory,
):
    user = await user_factory(email="u@example.com")

    with pytest.raises(NotFound):
        await notification_service.mark_notification_as_read(
            db_session,
            notification_id=999999,
            current_user=user,
        )
