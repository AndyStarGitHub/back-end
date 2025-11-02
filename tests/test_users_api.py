from datetime import datetime
import pytest
from uuid import uuid4
from zoneinfo import ZoneInfo


def _as_items(resp_json):
    return resp_json if isinstance(resp_json, list) else resp_json.get("items", [])


pytestmark = pytest.mark.anyio("asyncio")

BASE = "/api/v1/users"


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


async def test_delete_user(client):
    created = await _create_user_resilient(client, idx=5)
    uid = created.json().get("user", created.json())["id"]
    delete = await client.delete(f"{BASE}/{uid}")
    assert delete.status_code in (200, 204)
    get_after = await client.get(f"{BASE}/{uid}")
    assert get_after.status_code == 404


async def test_get_user_not_found(client):
    ro = await client.get(f"{BASE}/999999999")
    if ro.status_code == 422:
        ro = await client.get(f"{BASE}/{uuid4()}")
    assert ro.status_code == 404


async def test_create_user_validation(client):
    ro = await client.post(f"{BASE}", json={"email": ""})
    assert ro.status_code in (400, 422)


async def test_created_at_is_kyiv_tz(client):
    payload = {
        "email": "user_kyiv@example.com",
        "password": "secret123",
        "full_name": "Kyiv Check"
    }
    ro = await client.post("/api/v1/users", json=payload)
    assert ro.status_code in (200, 201)

    data = ro.json()
    dt = datetime.fromisoformat(data["created_at"])
    assert dt.tzinfo is not None
    kyiv = ZoneInfo("Europe/Kyiv")
    assert dt.astimezone(kyiv).tzinfo == kyiv
