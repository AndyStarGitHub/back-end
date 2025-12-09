import pytest

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.notification import NotificationService
from app.repositories.notification import NotificationRepository
from app.models.notification import NotificationStatusEnum
from app.core.errors import Forbidden

notification_service = NotificationService()
notification_repo = NotificationRepository()


@pytest.mark.asyncio
async def test_list_my_notifications_returns_only_current_user(
    db_session: AsyncSession,
    user_factory,
):
    user1 = await user_factory(email="notif_user1@example.com")
    user2 = await user_factory(email="notif_user2@example.com")

    await notification_repo.create_one(
        db_session,
        user_id=user1.id,
        company_id=None,
        quiz_id=None,
        message="Hello user1 - 1",
        status=NotificationStatusEnum.UNREAD,
    )
    await notification_repo.create_one(
        db_session,
        user_id=user1.id,
        company_id=None,
        quiz_id=None,
        message="Hello user1 - 2",
        status=NotificationStatusEnum.UNREAD,
    )
    await notification_repo.create_one(
        db_session,
        user_id=user2.id,
        company_id=None,
        quiz_id=None,
        message="Hello user2",
        status=NotificationStatusEnum.UNREAD,
    )

    resp = await notification_service.list_my_notifications(
        db_session,
        current_user=user1,
        offset=0,
        limit=50,
    )

    assert resp.total == 2
    assert len(resp.items) == 2
    assert all(item.user_id == user1.id for item in resp.items)
    messages = {item.message for item in resp.items}
    assert "Hello user1 - 1" in messages
    assert "Hello user1 - 2" in messages


@pytest.mark.asyncio
async def test_mark_notification_as_read_and_forbidden_for_other_user(
    db_session: AsyncSession,
    user_factory,
):
    owner = await user_factory(email="notif_owner@example.com")
    other_user = await user_factory(email="notif_other@example.com")

    notif = await notification_repo.create_one(
        db_session,
        user_id=owner.id,
        company_id=None,
        quiz_id=None,
        message="Owner notification",
        status=NotificationStatusEnum.UNREAD,
    )

    updated = await notification_service.mark_notification_as_read(
        db_session,
        notification_id=notif.id,
        current_user=owner,
    )

    assert updated.id == notif.id
    assert updated.status == NotificationStatusEnum.READ

    with pytest.raises(Forbidden):
        await notification_service.mark_notification_as_read(
            db_session,
            notification_id=notif.id,
            current_user=other_user,
        )
