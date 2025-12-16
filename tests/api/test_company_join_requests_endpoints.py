import pytest

pytestmark = pytest.mark.anyio


async def test_list_company_join_requests_forbidden_for_non_owner(
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
        f"/api/v1/company-join-requests/companies/{company.id}",
    )

    assert resp.status_code == 403
