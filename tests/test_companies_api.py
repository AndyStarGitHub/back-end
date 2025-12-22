from __future__ import annotations

from uuid import UUID

import pytest
from httpx import AsyncClient

from app.main import app
from app.core.deps import get_current_user
from app.schemas.company import CompanyVisibility


class DummyUser:
    def __init__(self, id: int) -> None:
        self.id = id


@pytest.mark.anyio
async def test_create_company_ok(client: AsyncClient):

    def override_current_user():
        return DummyUser(id=1)

    app.dependency_overrides[get_current_user] = override_current_user

    payload = {
        "name": "Test Company",
        "description": "Integration test company",
    }

    resp = await client.post("/api/v1/companies", json=payload)
    app.dependency_overrides.pop(get_current_user, None)

    assert resp.status_code == 201, resp.text
    data = resp.json()

    assert data["name"] == payload["name"]
    assert data["description"] == payload["description"]
    assert data["visibility"] == CompanyVisibility.public
    assert data["owner_id"] == 1
    UUID(data["id"])


@pytest.mark.anyio
async def test_create_company_can_set_public_visibility(client: AsyncClient):

    def override_current_user():
        return DummyUser(id=1)

    app.dependency_overrides[get_current_user] = override_current_user

    payload = {
        "name": "Public Company",
        "description": None,
        "visibility": CompanyVisibility.public.value,
    }

    resp = await client.post("/api/v1/companies", json=payload)
    app.dependency_overrides.pop(get_current_user, None)

    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["visibility"] == CompanyVisibility.public.value


@pytest.mark.anyio
async def test_owner_can_see_hidden_company(client: AsyncClient):

    def owner_dep():
        return DummyUser(id=1)

    app.dependency_overrides[get_current_user] = owner_dep
    create_resp = await client.post(
        "/api/v1/companies",
        json={
            "name": "Hidden Co",
            "description": None,
            "visibility": CompanyVisibility.hidden
        },
    )
    assert create_resp.status_code == 201, create_resp.text
    created = create_resp.json()
    company_id = created["id"]

    get_resp = await client.get(f"/api/v1/companies/{company_id}")
    app.dependency_overrides.pop(get_current_user, None)

    assert get_resp.status_code == 200, get_resp.text
    data = get_resp.json()
    assert data["id"] == company_id
    assert data["visibility"] == CompanyVisibility.hidden.value


@pytest.mark.anyio
async def test_non_owner_cannot_see_hidden_company(client: AsyncClient):

    def owner_dep():
        return DummyUser(id=1)

    def other_dep():
        return DummyUser(id=2)

    app.dependency_overrides[get_current_user] = owner_dep
    create_resp = await client.post(
        "/api/v1/companies",
        json={
            "name": "Secret Co",
            "description": None,
            "visibility": CompanyVisibility.hidden
        },
    )
    assert create_resp.status_code == 201, create_resp.text
    created = create_resp.json()
    company_id = created["id"]

    app.dependency_overrides[get_current_user] = other_dep
    get_resp = await client.get(f"/api/v1/companies/{company_id}")
    app.dependency_overrides.pop(get_current_user, None)

    assert get_resp.status_code == 404, get_resp.text


@pytest.mark.anyio
async def test_update_company_owner_ok(client: AsyncClient):

    def owner_dep():
        return DummyUser(id=1)

    app.dependency_overrides[get_current_user] = owner_dep

    create_resp = await client.post(
        "/api/v1/companies",
        json={"name": "Old Name", "description": "Old desc"},
    )
    assert create_resp.status_code == 201, create_resp.text
    created = create_resp.json()
    company_id = created["id"]

    update_resp = await client.patch(
        f"/api/v1/companies/{company_id}",
        json={
            "name": "New Name",
            "visibility": CompanyVisibility.public.value,
        },
    )
    app.dependency_overrides.pop(get_current_user, None)

    assert update_resp.status_code == 200, update_resp.text
    updated = update_resp.json()
    assert updated["name"] == "New Name"
    assert updated["visibility"] == CompanyVisibility.public.value


@pytest.mark.anyio
async def test_update_company_non_owner_forbidden(client: AsyncClient):

    def owner_dep():
        return DummyUser(id=1)

    def other_dep():
        return DummyUser(id=2)

    app.dependency_overrides[get_current_user] = owner_dep
    create_resp = await client.post(
        "/api/v1/companies",
        json={"name": "Foreign Co", "description": None},
    )
    assert create_resp.status_code == 201, create_resp.text
    created = create_resp.json()
    company_id = created["id"]

    app.dependency_overrides[get_current_user] = other_dep
    update_resp = await client.patch(
        f"/api/v1/companies/{company_id}",
        json={"name": "Hacked Name"},
    )
    app.dependency_overrides.pop(get_current_user, None)

    assert update_resp.status_code == 403, update_resp.text


@pytest.mark.anyio
async def test_delete_company_owner_ok(client: AsyncClient):

    def owner_dep():
        return DummyUser(id=1)

    app.dependency_overrides[get_current_user] = owner_dep

    create_resp = await client.post(
        "/api/v1/companies",
        json={"name": "To Delete", "description": None},
    )
    assert create_resp.status_code == 201, create_resp.text
    created = create_resp.json()
    company_id = created["id"]

    delete_resp = await client.delete(f"/api/v1/companies/{company_id}")
    assert delete_resp.status_code == 204, delete_resp.text

    get_resp = await client.get(f"/api/v1/companies/{company_id}")
    app.dependency_overrides.pop(get_current_user, None)

    assert get_resp.status_code == 404, get_resp.text


@pytest.mark.anyio
async def test_list_public_and_my_companies(client: AsyncClient):

    def user1_dep():
        return DummyUser(id=1)

    def user2_dep():
        return DummyUser(id=2)

    app.dependency_overrides[get_current_user] = user1_dep
    resp1 = await client.post(
        "/api/v1/companies",
        json={
            "name": "User1 Hidden",
            "description": None,
            "visibility": CompanyVisibility.hidden.value,
        },
    )
    assert resp1.status_code == 201, resp1.text

    resp2 = await client.post(
        "/api/v1/companies",
        json={
            "name": "User1 Public",
            "description": None,
            "visibility": CompanyVisibility.public.value,
        },
    )
    assert resp2.status_code == 201, resp2.text
    created_public = resp2.json()
    public_id = created_public["id"]

    update_resp = await client.patch(
        f"/api/v1/companies/{public_id}",
        json={"visibility": CompanyVisibility.public.value},
    )
    assert update_resp.status_code == 200, update_resp.text

    app.dependency_overrides[get_current_user] = user2_dep
    resp3 = await client.post(
        "/api/v1/companies",
        json={
            "name": "User2 Hidden",
            "description": None,
            "visibility": CompanyVisibility.hidden.value,
        },
    )
    assert resp3.status_code == 201, resp3.text

    app.dependency_overrides.pop(get_current_user, None)
    list_public = await client.get("/api/v1/companies")
    assert list_public.status_code == 200, list_public.text
    data_public = list_public.json()
    names_public = [item["name"] for item in data_public["items"]]

    assert "User1 Public" in names_public
    assert "User1 Hidden" not in names_public
    assert "User2 Hidden" not in names_public

    app.dependency_overrides[get_current_user] = user1_dep
    list_me_1 = await client.get("/api/v1/companies/me")
    assert list_me_1.status_code == 200, list_me_1.text
    data_me_1 = list_me_1.json()
    names_me_1 = [item["name"] for item in data_me_1["items"]]

    assert "User1 Public" in names_me_1
    assert "User1 Hidden" in names_me_1
    assert "User2 Hidden" not in names_me_1

    app.dependency_overrides[get_current_user] = user2_dep
    list_me_2 = await client.get("/api/v1/companies/me")
    app.dependency_overrides.pop(get_current_user, None)

    assert list_me_2.status_code == 200, list_me_2.text
    data_me_2 = list_me_2.json()
    names_me_2 = [item["name"] for item in data_me_2["items"]]

    assert "User2 Hidden" in names_me_2
    assert "User1 Public" not in names_me_2
    assert "User1 Hidden" not in names_me_2


@pytest.mark.anyio
async def test_create_company_invalid_visibility_422(client: AsyncClient):

    def override_current_user():
        return DummyUser(id=1)

    app.dependency_overrides[get_current_user] = override_current_user

    resp = await client.post(
        "/api/v1/companies",
        json={
            "name": "Bad Co",
            "description": None,
            "visibility": "wrong"
        },
    )
    app.dependency_overrides.pop(get_current_user, None)

    assert resp.status_code == 422, resp.text

    @pytest.mark.anyio
    async def test_create_company_default_visibility_is_public(
            client: AsyncClient
    ):
        def override_current_user():
            return DummyUser(id=1)

        app.dependency_overrides[get_current_user] = override_current_user

        resp = await client.post(
            "/api/v1/companies",
            json={"name": "Default Public Co", "description": None},
        )
        app.dependency_overrides.pop(get_current_user, None)

        assert resp.status_code == 201, resp.text
        assert resp.json()["visibility"] == CompanyVisibility.public.value
