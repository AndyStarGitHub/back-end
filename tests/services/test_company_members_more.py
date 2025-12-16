import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import Forbidden, NotFound
from app.services.company_members import member_service

pytestmark = pytest.mark.anyio


async def test_remove_member_owner_cannot_be_removed(
    db_session: AsyncSession,
    user_factory,
    company_factory,
):
    owner = await user_factory(email="owner@example.com")
    company = await company_factory(owner=owner)

    with pytest.raises(Forbidden):
        await member_service.remove_member_from_company(
            db=db_session,
            company_id=company.id,
            member_user_id=owner.id,
            current_user=owner,
        )


async def test_leave_company_owner_cannot_leave(
    db_session: AsyncSession,
    user_factory,
    company_factory,
):
    owner = await user_factory(email="owner@example.com")
    company = await company_factory(owner=owner)

    with pytest.raises(Forbidden):
        await member_service.leave_company(
            db=db_session,
            company_id=company.id,
            current_user=owner,
        )


async def test_leave_company_user_not_member_forbidden(
    db_session: AsyncSession,
    user_factory,
    company_factory,
):
    owner = await user_factory(email="owner@example.com")
    user = await user_factory(email="u@example.com")
    company = await company_factory(owner=owner)

    with pytest.raises(Forbidden):
        await member_service.leave_company(
            db=db_session,
            company_id=company.id,
            current_user=user,
        )
