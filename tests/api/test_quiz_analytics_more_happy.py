import pytest

pytestmark = pytest.mark.anyio


async def test_my_quiz_analytics_last_attempts_happy_path_returns_200(
    client,
    override_current_user,
    user_factory,
):
    user = await user_factory(email="me@example.com")
    override_current_user(user)

    resp = await client.get("/api/v1/me/quiz_analytics/last-attempts")
    assert resp.status_code == 200

    data = resp.json()
    assert isinstance(data, dict)
