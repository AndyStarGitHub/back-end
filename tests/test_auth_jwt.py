import jwt
import pytest

from app.core.config import settings

BASE_USERS = "/api/v1/users"
AUTH_BASE = "/api/v1/auth"


@pytest.mark.anyio
async def test_login_returns_access_and_refresh(client):
    payload = {
        "email": "jwt_login_user@example.com",
        "password": "secret123",
        "full_name": "JWT Login User",
    }
    created = await client.post(BASE_USERS, json=payload)
    assert created.status_code in (200, 201)
    user_data = created.json()
    user_id = user_data.get("id") or user_data.get("user", {}).get("id")
    assert user_id is not None

    login_resp = await client.post(
        f"{AUTH_BASE}/login",
        json={"email": payload["email"], "password": payload["password"]},
    )
    assert login_resp.status_code == 200
    tokens = login_resp.json()

    assert "access_token" in tokens
    assert "refresh_token" in tokens
    assert tokens.get("token_type") == "bearer"

    access_token = tokens["access_token"]
    refresh_token = tokens["refresh_token"]

    access_payload = jwt.decode(
        access_token,
        settings.security.JWT_SECRET,
        algorithms=[settings.security.JWT_ALG],
    )
    assert access_payload["sub"] == str(user_id)
    assert access_payload["email"] == payload["email"]
    assert access_payload["type"] == "access"

    refresh_payload = jwt.decode(
        refresh_token,
        settings.security.JWT_REFRESH_SECRET,
        algorithms=[settings.security.JWT_REFRESH_ALG],
    )
    assert refresh_payload["sub"] == str(user_id)
    assert refresh_payload["type"] == "refresh"


@pytest.mark.anyio
async def test_refresh_returns_new_access_token(client):
    payload = {
        "email": "refresh_user@example.com",
        "password": "secret123",
        "full_name": "Refresh User",
    }
    created = await client.post(BASE_USERS, json=payload)
    assert created.status_code in (200, 201)

    login_resp = await client.post(
        f"{AUTH_BASE}/login",
        json={"email": payload["email"], "password": payload["password"]},
    )
    assert login_resp.status_code == 200
    tokens = login_resp.json()
    old_access = tokens["access_token"]
    refresh = tokens["refresh_token"]

    refresh_resp = await client.post(
        f"{AUTH_BASE}/refresh",
        json={"refresh_token": refresh},
    )
    assert refresh_resp.status_code == 200
    body = refresh_resp.json()

    assert "access_token" in body
    new_access = body["access_token"]
    assert new_access != old_access

    access_payload = jwt.decode(
        new_access,
        settings.security.JWT_SECRET,
        algorithms=[settings.security.JWT_ALG],
    )
    assert access_payload["email"] == payload["email"]
    assert access_payload["type"] == "access"


@pytest.mark.anyio
async def test_refresh_rejects_access_token(client):
    payload = {
        "email": "bad_refresh_user@example.com",
        "password": "secret123",
        "full_name": "Bad Refresh User",
    }
    created = await client.post(BASE_USERS, json=payload)
    assert created.status_code in (200, 201)

    login_resp = await client.post(
        f"{AUTH_BASE}/login",
        json={"email": payload["email"], "password": payload["password"]},
    )
    assert login_resp.status_code == 200
    tokens = login_resp.json()
    access = tokens["access_token"]

    refresh_resp = await client.post(
        f"{AUTH_BASE}/refresh",
        json={"refresh_token": access},
    )

    assert refresh_resp.status_code in (400, 401)
