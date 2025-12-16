import pytest
from app.models.company_member import CompanyMemberRoleEnum

pytestmark = pytest.mark.anyio


async def test_get_my_memberships_ok(
    client,
    override_current_user,
    user_factory,
    company_factory,
    company_member_factory,
):
    user = await user_factory(email="member@example.com")
    owner = await user_factory(email="owner@example.com")
    company = await company_factory(owner=owner)

    await company_member_factory(
        company=company,
        user=user,
        role=CompanyMemberRoleEnum.MEMBER
    )

    override_current_user(user)

    resp = await client.get("/api/v1/company-members/me")
    assert resp.status_code == 200
    data = resp.json()

    assert "items" in data
    assert data["total"] >= 1


async def test_remove_member_forbidden_for_non_owner(
    client,
    override_current_user,
    user_factory,
    company_factory,
    company_member_factory,
):
    owner = await user_factory(email="owner@example.com")
    other = await user_factory(email="other@example.com")
    member = await user_factory(email="member@example.com")
    company = await company_factory(owner=owner)

    await company_member_factory(company=company, user=member)

    override_current_user(other)

    resp = await client.delete(
        f"/api/v1/company-members/{company.id}/members/{member.id}"
    )
    assert resp.status_code == 403
