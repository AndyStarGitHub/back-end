import pytest

pytestmark = pytest.mark.anyio


async def test_login_validation_422(client):
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "u@example.com"}
    )
    assert resp.status_code == 422


async def test_me_unauthorized_401(client, override_current_user):
    override_current_user(None)
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401
