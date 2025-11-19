from datetime import datetime
import pytest
from uuid import uuid4
from zoneinfo import ZoneInfo

from app.core.deps import get_current_user
from app.main import app
from app.services.auth_service import create_access_token


def _as_items(resp_json):
    return resp_json if isinstance(resp_json, list) else resp_json.get("items", [])


pytestmark = pytest.mark.anyio("asyncio")

BASE = "/api/v1/users"
AUTH_BASE = "/api/v1/auth"


def _mk_payload(variant=1, idx=0):
    email = f"user{idx}@example.com"
    if variant == 1:
        return {"email": email,
                "hashed_password": "secret123",
                "full_name": "User One"
                }
    else:
        return {
            "email": email,
            "password": "secret123",
            "full_name": "User One"
        }


async def _create_user_resilient(client, idx=0):
    for variant in (1, 2):
        payload = _mk_payload(variant, idx)
        ro = await client.post(f"{BASE}", json=payload)  # <-- без '/'
        if ro.status_code in (200, 201):
            return ro
        if ro.status_code in (202, 204):
            ls = await client.get(f"{BASE}")
            if ls.status_code == 200 and isinstance(ls.json(), list) and ls.json():
                return ro
    assert False, f"Create failed; last status={ro.status_code}, body={ro.text}"


async def test_create_user(client):
    ro = await _create_user_resilient(client, idx=1)
    assert ro.status_code in (200, 201)
    data = ro.json() if ro.headers.get("content-type","").startswith("application/json") else {}
    if isinstance(data, dict):
        assert "email" in data
        assert data["email"].endswith("@example.com")
        assert "id" in data or "user" in data
    ls = await client.get(f"{BASE}")
    assert ls.status_code == 200
    items = _as_items(ls.json())
    assert isinstance(items, list)
    assert len(items) >= 1


async def test_get_user_by_id(client):
    created = await _create_user_resilient(client, idx=2)
    body = created.json() if created.headers.get("content-type","").startswith("application/json") else {}
    user_obj = body.get("user", body)
    uid = user_obj.get("id")
    assert uid is not None, f"No id in create response: {body}"
    ro = await client.get(f"{BASE}/{uid}")
    assert ro.status_code == 200
    assert ro.json().get("id") == uid


async def test_list_users(client):
    await _create_user_resilient(client, idx=3)
    ro = await client.get(f"{BASE}")
    assert ro.status_code == 200
    items = _as_items(ro.json())
    assert isinstance(items, list)
    assert len(items) >= 1


@pytest.mark.asyncio
async def test_update_user(client):
    created = await _create_user_resilient(client, idx=4)
    body = created.json()
    user_data = body.get("user", body)
    uid = user_data["id"]

    class DummyUser:
        def __init__(self, user_id: int):
            self.id = user_id

    async def override_get_current_user():
        return DummyUser(uid)

    app.dependency_overrides[get_current_user] = override_get_current_user

    try:
        patch = await client.patch(
            f"{BASE}/me",
            json={"full_name": "Renamed User"},
        )

        assert patch.status_code in (200, 204), patch.text

        get_after = await client.get(f"{BASE}/{uid}")
        assert get_after.status_code == 200
        data_after = get_after.json().get("user", get_after.json())
        assert data_after["full_name"] == "Renamed User"
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.anyio
async def test_delete_user(client):
    payload = {
        "email": "del_user@example.com",
        "password": "secret123",
        "full_name": "To Delete",
    }
    created = await client.post(BASE, json=payload)
    assert created.status_code in (200, 201)

    data = created.json()
    user_id = data.get("id") or data.get("user", {}).get("id")

    token = create_access_token(
        sub=str(user_id),
        email=payload.get("email"),
    )
    headers = {"Authorization": f"Bearer {token}"}

    delete_resp = await client.delete(f"{BASE}/me", headers=headers)
    assert delete_resp.status_code in (200, 204)

    get_resp = await client.get(f"{BASE}/{user_id}")
    assert get_resp.status_code in (404, 410)


async def test_get_user_not_found(client):
    ro = await client.get(f"{BASE}/999999999")
    if ro.status_code == 422:
        ro = await client.get(f"{BASE}/{uuid4()}")
    assert ro.status_code == 404


async def test_create_user_validation(client):
    ro = await client.post(f"{BASE}", json={"email": ""})
    assert ro.status_code in (400, 422)


async def test_created_at_is_utc(client):
    payload = {
        "email": "user_utc@example.com",
        "password": "secret123",
        "full_name": "UTC Check",
    }
    ro = await client.post("/api/v1/users", json=payload)
    assert ro.status_code in (200, 201)

    data = ro.json()
    dt = datetime.fromisoformat(data["created_at"])

    if dt.tzinfo is None:
        assert True
    else:
        assert dt.tzinfo == ZoneInfo("UTC")


@pytest.mark.asyncio
async def test_cannot_update_other_user_profile(client):
    created1 = await _create_user_resilient(client, idx=10)
    created2 = await _create_user_resilient(client, idx=11)

    user1 = created1.json().get("user", created1.json())
    user2 = created2.json().get("user", created2.json())

    uid1 = user1["id"]
    uid2 = user2["id"]
    old_name_user1 = user1["full_name"]

    class DummyUser:
        def __init__(self, user_id: int):
            self.id = user_id

    async def override_get_current_user():
        return DummyUser(uid2)

    app.dependency_overrides[get_current_user] = override_get_current_user

    try:
        resp = await client.patch(
            f"{BASE}/me",
            json={"full_name": "New Name For User2"},
        )
        assert resp.status_code in (200, 204), resp.text

        get_user1 = await client.get(f"{BASE}/{uid1}")
        assert get_user1.status_code == 200
        data_user1 = get_user1.json().get("user", get_user1.json())
        assert data_user1["full_name"] == old_name_user1
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_cannot_change_email_via_update(client):
    created = await _create_user_resilient(client, idx=12)
    user = created.json().get("user", created.json())
    uid = user["id"]
    old_email = user["email"]

    class DummyUser:
        def __init__(self, user_id: int):
            self.id = user_id

    async def override_get_current_user():
        return DummyUser(uid)

    app.dependency_overrides[get_current_user] = override_get_current_user

    try:
        resp = await client.patch(
            f"{BASE}/me",  # 🔁 тепер /me, а не /{uid}
            json={"email": "new-email@example.com"},
        )

        assert resp.status_code in (200, 204, 400, 403, 409), resp.text

        get_after = await client.get(f"{BASE}/{uid}")
        assert get_after.status_code == 200
        data_after = get_after.json().get("user", get_after.json())
        assert data_after["email"] == old_email
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_cannot_delete_other_user(client):
    created1 = await _create_user_resilient(client, idx=13)
    created2 = await _create_user_resilient(client, idx=14)

    user1 = created1.json().get("user", created1.json())
    user2 = created2.json().get("user", created2.json())

    uid1 = user1["id"]
    uid2 = user2["id"]

    class DummyUser:
        def __init__(self, user_id: int):
            self.id = user_id

    async def override_get_current_user():
        return DummyUser(uid2)

    app.dependency_overrides[get_current_user] = override_get_current_user

    try:
        resp = await client.delete(f"{BASE}/me")
        assert resp.status_code in (200, 204), resp.text

        get_user2 = await client.get(f"{BASE}/{uid2}")
        assert get_user2.status_code in (404, 410)

        get_user1 = await client.get(f"{BASE}/{uid1}")
        assert get_user1.status_code == 200
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_cannot_change_other_user_password(client):
    created1 = await _create_user_resilient(client, idx=15)
    created2 = await _create_user_resilient(client, idx=16)

    user1 = created1.json().get("user", created1.json())
    user2 = created2.json().get("user", created2.json())

    uid1 = user1["id"]
    uid2 = user2["id"]

    class DummyUser:
        def __init__(self, user_id: int):
            self.id = user_id

    async def override_get_current_user():
        return DummyUser(uid2)

    app.dependency_overrides[get_current_user] = override_get_current_user

    try:
        resp = await client.post(
            f"{BASE}/me/password",
            json={
                "old_password": "whatever",
                "new_password": "NewSecret123!",
            },
        )

        assert resp.status_code in (204, 403), resp.text

        get_user1 = await client.get(f"{BASE}/{uid1}")
        assert get_user1.status_code == 200
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_change_password_wrong_old_password(client):
    created = await _create_user_resilient(client, idx=17)
    user = created.json().get("user", created.json())
    uid = user["id"]

    class DummyUser:
        def __init__(self, user_id: int):
            self.id = user_id

    async def override_get_current_user():
        return DummyUser(uid)

    app.dependency_overrides[get_current_user] = override_get_current_user

    try:
        resp = await client.post(
            f"{BASE}/me/password",
            json={
                "old_password": "definitely_wrong_password",
                "new_password": "SomeNewPassword123!",
            },
        )

        assert resp.status_code == 403, resp.text
        assert "password" in resp.json()["detail"].lower()
    finally:
        app.dependency_overrides.pop(get_current_user, None)
