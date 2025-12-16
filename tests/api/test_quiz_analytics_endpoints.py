import pytest

pytestmark = pytest.mark.anyio


async def test_quiz_analytics_requires_auth_401(client, override_current_user):
    override_current_user(None)
    resp = await client.get("/api/v1/me/quiz_analytics/overall-rating")
    assert resp.status_code == 401
