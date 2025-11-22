import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.errors import Forbidden
from app.models.company_member import CompanyMember, CompanyMemberRoleEnum
from app.models.user import User
from app.services.company_admin_service import (
    assign_admin,
    remove_admin,
    list_admins,
)


@pytest.mark.anyio
async def test_owner_can_make_member_admin(
    db_session: AsyncSession,
    user_factory,
    company_factory,
):
    owner: User = await user_factory(email="owner@example.com")
    company = await company_factory(owner=owner)

    member_user: User = await user_factory(email="member@example.com")

    member = CompanyMember(
        company_id=company.id,
        user_id=member_user.id,
    )
    db_session.add(member)
    await db_session.commit()
    await db_session.refresh(member)

    assert member.role == CompanyMemberRoleEnum.MEMBER

    await assign_admin(
        db=db_session,
        company_id=company.id,
        member_user_id=member_user.id,
        current_user=owner,
    )

    res = await db_session.execute(
        select(CompanyMember).where(
            CompanyMember.company_id == company.id,
            CompanyMember.user_id == member_user.id,
        )
    )
    updated_member = res.scalars().one()
    assert updated_member.role == CompanyMemberRoleEnum.ADMIN


@pytest.mark.anyio
async def test_non_owner_cannot_make_member_admin(
    db_session: AsyncSession,
    user_factory,
    company_factory,
):
    owner: User = await user_factory(email="owner2@example.com")
    company = await company_factory(owner=owner)

    not_owner: User = await user_factory(email="not_owner@example.com")

    member_user: User = await user_factory(email="member2@example.com")
    member = CompanyMember(
        company_id=company.id,
        user_id=member_user.id,
    )
    db_session.add(member)
    await db_session.commit()

    with pytest.raises(Forbidden):
        await assign_admin(
            db=db_session,
            company_id=company.id,
            member_user_id=member_user.id,
            current_user=not_owner,
        )


@pytest.mark.anyio
async def test_cannot_make_non_member_admin(
    db_session: AsyncSession,
    user_factory,
    company_factory,
):

    owner: User = await user_factory(email="owner3@example.com")
    company = await company_factory(owner=owner)

    outsider: User = await user_factory(email="outsider@example.com")

    with pytest.raises(Forbidden):
        await assign_admin(
            db=db_session,
            company_id=company.id,
            member_user_id=outsider.id,
            current_user=owner,
        )


@pytest.mark.anyio
async def test_owner_can_remove_member_admin(
    db_session: AsyncSession,
    user_factory,
    company_factory,
):

    owner: User = await user_factory(email="owner4@example.com")
    company = await company_factory(owner=owner)

    member_user: User = await user_factory(email="member4@example.com")
    member = CompanyMember(
        company_id=company.id,
        user_id=member_user.id,
        role=CompanyMemberRoleEnum.ADMIN,
    )
    db_session.add(member)
    await db_session.commit()

    await remove_admin(
        db=db_session,
        company_id=company.id,
        member_user_id=member_user.id,
        current_user=owner,
    )

    res = await db_session.execute(
        select(CompanyMember).where(
            CompanyMember.company_id == company.id,
            CompanyMember.user_id == member_user.id,
        )
    )
    updated_member = res.scalars().one()
    assert updated_member.role == CompanyMemberRoleEnum.MEMBER


@pytest.mark.anyio
async def test_list_company_admins_returns_only_admins(
    db_session: AsyncSession,
    user_factory,
    company_factory,
):

    owner: User = await user_factory(email="owner5@example.com")
    company = await company_factory(owner=owner)

    admin_user: User = await user_factory(email="admin_user@example.com")
    admin_member = CompanyMember(
        company_id=company.id,
        user_id=admin_user.id,
        role=CompanyMemberRoleEnum.ADMIN,
    )

    regular_user: User = await user_factory(email="regular_user@example.com")
    regular_member = CompanyMember(
        company_id=company.id,
        user_id=regular_user.id,
        role=CompanyMemberRoleEnum.MEMBER,
    )

    db_session.add_all([admin_member, regular_member])
    await db_session.commit()

    admins = await list_admins(
        db=db_session,
        company_id=company.id,
        current_user=owner,
    )

    assert len(admins) == 1
    assert admins[0].id == admin_user.id
