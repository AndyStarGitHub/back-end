import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import Forbidden
from app.models.company_member import CompanyMember
from app.services.company_members import member_service


pytestmark = pytest.mark.anyio


async def test_list_company_members_returns_users(
    db_session: AsyncSession,
    user_factory,
    company_factory,
):
    owner = await user_factory(email="owner@example.com")
    user1 = await user_factory(email="member1@example.com")
    user2 = await user_factory(email="member2@example.com")
    company = await company_factory(owner=owner)

    db_session.add(CompanyMember(company_id=company.id, user_id=user1.id))
    db_session.add(CompanyMember(company_id=company.id, user_id=user2.id))
    await db_session.commit()

    users = await member_service.list_company_members(
        db=db_session,
        company_id=company.id,
        limit=10,
        offset=0,
    )

    emails = {u.email for u in users}
    assert "member1@example.com" in emails
    assert "member2@example.com" in emails


async def test_owner_can_remove_member(
    db_session: AsyncSession,
    user_factory,
    company_factory,
):
    owner = await user_factory(email="owner@example.com")
    member = await user_factory(email="member@example.com")
    company = await company_factory(owner=owner)

    db_session.add(CompanyMember(company_id=company.id, user_id=member.id))
    await db_session.commit()

    await member_service.remove_member_from_company(
        db=db_session,
        company_id=company.id,
        member_user_id=member.id,
        current_user=owner,
    )

    result = await db_session.execute(
        CompanyMember.__table__.select().where(
            CompanyMember.company_id == company.id,
            CompanyMember.user_id == member.id,
        )
    )
    assert result.first() is None


async def test_non_owner_cannot_remove_member(
    db_session: AsyncSession,
    user_factory,
    company_factory,
):
    owner = await user_factory(email="owner@example.com")
    member = await user_factory(email="member@example.com")
    other = await user_factory(email="other@example.com")
    company = await company_factory(owner=owner)

    db_session.add(CompanyMember(company_id=company.id, user_id=member.id))
    await db_session.commit()

    with pytest.raises(Forbidden):
        await member_service.remove_member_from_company(
            db=db_session,
            company_id=company.id,
            member_user_id=member.id,
            current_user=other,
        )


async def test_user_can_leave_company(
    db_session: AsyncSession,
    user_factory,
    company_factory,
):
    owner = await user_factory(email="owner@example.com")
    member = await user_factory(email="member@example.com")
    company = await company_factory(owner=owner)

    db_session.add(CompanyMember(company_id=company.id, user_id=member.id))
    await db_session.commit()

    await member_service.leave_company(
        db=db_session,
        company_id=company.id,
        current_user=member,
    )

    result = await db_session.execute(
        CompanyMember.__table__.select().where(
            CompanyMember.company_id == company.id,
            CompanyMember.user_id == member.id,
        )
    )
    assert result.first() is None


async def test_owner_cannot_leave_company(
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
