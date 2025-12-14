import pytest

pytestmark = pytest.mark.anyio


async def test_create_company_success(
        client,
        override_current_user,
        user_factory
):
    user = await user_factory(email="owner@example.com")
    override_current_user(user)

    resp = await client.post("/api/v1/companies", json={"name": "Test Co"})
    assert resp.status_code in (200, 201)

    data = resp.json()
    assert data["name"] == "Test Co"
    assert data["owner_id"] == user.id


async def test_update_company_forbidden_for_non_owner(
    client,
    override_current_user,
    user_factory,
    company_factory,
):
    owner = await user_factory(email="owner@example.com")
    other = await user_factory(email="other@example.com")
    company = await company_factory(owner=owner)

    override_current_user(other)

    resp = await client.patch(
        f"/api/v1/companies/{company.id}",
        json={"name": "New Name"}
    )
    assert resp.status_code == 403


async def test_list_companies_public_ok(client):
    resp = await client.get("/api/v1/companies")
    assert resp.status_code == 200
