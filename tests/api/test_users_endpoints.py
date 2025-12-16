import pytest

pytestmark = pytest.mark.anyio


async def test_register_validation_password_too_short_422(client):
    resp = await client.post(
        "/api/v1/users",
        json={"email": "u@example.com", "password": "pw"},
    )
    assert resp.status_code == 422


async def test_users_me_returns_current_user(
        client,
        override_current_user,
        user_factory
):
    user = await user_factory(email="me@example.com")
    override_current_user(user)

    resp = await client.get("/api/v1/users/me")
    assert resp.status_code == 200

    data = resp.json()
    assert data["id"] == user.id
    assert data["email"] == user.email


async def test_get_user_by_id_404(client):
    resp = await client.get("/api/v1/users/999999")
    assert resp.status_code == 404
