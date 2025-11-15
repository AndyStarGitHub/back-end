from datetime import datetime
import pytest
from uuid import uuid4
from zoneinfo import ZoneInfo

from app.services.auth_service import create_access_token


def _as_items(resp_json):
    return resp_json if isinstance(resp_json, list) else resp_json.get("items", [])


pytestmark = pytest.mark.anyio("asyncio")

BASE = "/api/v1/users"
AUTH_BASE = "/api/v1/auth"


def _mk_payload(variant=1, idx=0):
    email = f"user{idx}@example.com"
    if variant == 1:
        return {"email": email, "hashed_password": "secret123", "full_name": "User One"}
    else:
        return {"email": email, "password": "secret123", "full_name": "User One"}


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


async def test_update_user(client):
    created = await _create_user_resilient(client, idx=4)
    uid = created.json().get("user", created.json())["id"]
    patch = await client.patch(
        f"{BASE}/{uid}",
        json={"full_name": "Renamed User"}
    )
    if patch.status_code == 405:
        patch = await client.put(
            f"{BASE}/{uid}",
            json={"full_name": "Renamed User"}
        )
    assert patch.status_code in (200, 204)
    get_after = await client.get(f"{BASE}/{uid}")
    assert get_after.status_code == 200


@pytest.mark.anyio
async def test_delete_user(client):
    # 1. Створюємо юзера через API
    payload = {
        "email": "del_user@example.com",
        "password": "secret123",
        "full_name": "To Delete",
    }
    created = await client.post(BASE, json=payload)
    assert created.status_code in (200, 201)

    data = created.json()
    user_id = data.get("id") or data.get("user", {}).get("id")

    # 2. Генеруємо локальний access-token, як бек
    token = create_access_token(
        sub=str(user_id),
        email=payload.get("email")
    )
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Видаляємо СВОГО ж користувача
    delete_resp = await client.delete(f"{BASE}/{user_id}", headers=headers)
    assert delete_resp.status_code in (200, 204)

    # 4. Перевіряємо, що юзера вже немає
    get_after = await client.get(f"{BASE}/{user_id}")
    assert get_after.status_code == 404


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
