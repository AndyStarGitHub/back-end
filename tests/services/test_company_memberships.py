import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.company_members import member_service

pytestmark = pytest.mark.anyio


async def test_list_my_memberships_returns_two_companies(
    db_session: AsyncSession,
    user_factory,
    company_factory,
    company_member_factory,
):
    user = await user_factory(email="member@example.com")

    owner1 = await user_factory(email="owner1@example.com")
    owner2 = await user_factory(email="owner2@example.com")

    company1 = await company_factory(owner=owner1, name="Company 1")
    company2 = await company_factory(owner=owner2, name="Company 2")

    await company_member_factory(company=company1, user=user)
    await company_member_factory(company=company2, user=user)

    res = await member_service.list_my_memberships(
        db=db_session,
        current_user=user,
        offset=0,
        limit=50,
    )

    assert res.total == 2
    assert len(res.items) == 2

    company_ids = {item.company.id for item in res.items}
    assert company_ids == {company1.id, company2.id}
