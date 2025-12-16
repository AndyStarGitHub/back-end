import pytest

pytestmark = pytest.mark.anyio


async def test_list_notifications_unauthorized_401(
        client,
        override_current_user
):
    override_current_user(None)
    resp = await client.get("/api/v1/me/notifications/")
    assert resp.status_code == 401


async def test_mark_notification_as_read_404(
        client,
        override_current_user,
        user_factory
):
    user = await user_factory(email="u@example.com")
    override_current_user(user)
    resp = await client.patch(
        "/api/v1/me/notifications/00000000-0000-0000-0000-000000000000/read"
    )
    assert resp.status_code == 404
