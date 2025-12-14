import pytest

pytestmark = pytest.mark.anyio


async def test_create_invitation_201(
        client,
        override_current_user,
        user_factory,
        company_factory
):
    owner = await user_factory(email="owner@example.com")
    invited = await user_factory(email="invited@example.com")
    company = await company_factory(owner=owner)

    override_current_user(owner)

    resp = await client.post(
        f"/api/v1/company-invitations/companies/{company.id}",
        json={"invited_user_id": invited.id},
    )
    assert resp.status_code == 201

    data = resp.json()
    assert data["company_id"] == str(company.id)
    assert data["invited_user_id"] == invited.id


async def test_list_company_invitations_forbidden_for_non_owner(
    client,
    override_current_user,
    user_factory,
    company_factory,
):
    owner = await user_factory(email="owner@example.com")
    other = await user_factory(email="other@example.com")
    company = await company_factory(owner=owner)

    override_current_user(other)

    resp = await client.get(
        f"/api/v1/company-invitations/companies/{company.id}"
    )
    assert resp.status_code == 403
