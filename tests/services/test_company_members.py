import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import Forbidden
from app.models.company_member import CompanyMember, CompanyMemberRoleEnum
from app.services.company_members import member_service

from httpx import AsyncClient


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


async def test_company_members_me_unauthorized(client, override_current_user):
    override_current_user(None)

    r = await client.get("/api/v1/company-members/me")
    assert r.status_code == 401


async def test_company_members_me_returns_only_current_user_memberships(
    client,
    override_current_user,
    user_factory,
    company_factory,
    company_member_factory,
):
    u1 = await user_factory(email="u1@example.com")
    u2 = await user_factory(email="u2@example.com")

    c1 = await company_factory(
        owner=await user_factory(email="owner1@example.com")
    )
    c2 = await company_factory(
        owner=await user_factory(email="owner2@example.com")
    )

    await company_member_factory(
        company=c1,
        user=u1,
        role=CompanyMemberRoleEnum.MEMBER
    )
    await company_member_factory(
        company=c2,
        user=u1,
        role=CompanyMemberRoleEnum.ADMIN
    )

    await company_member_factory(
        company=c1,
        user=u2,
        role=CompanyMemberRoleEnum.MEMBER
    )

    override_current_user(u1)

    r = await client.get("/api/v1/company-members/me?offset=0&limit=50")
    assert r.status_code == 200

    data = r.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2

    company_ids = {item["company"]["id"] for item in data["items"]}
    assert str(c1.id) in company_ids
    assert str(c2.id) in company_ids


async def test_company_members_me_pagination(
    client,
    override_current_user,
    user_factory,
    company_factory,
    company_member_factory,
):
    u = await user_factory(email="u@example.com")
    owner = await user_factory(email="owner@example.com")

    companies = []
    for i in range(3):
        companies.append(await company_factory(owner=owner, name=f"C{i}"))

    for c in companies:
        await company_member_factory(
            company=c,
            user=u,
            role=CompanyMemberRoleEnum.MEMBER
        )

    override_current_user(u)

    r1 = await client.get("/api/v1/company-members/me?offset=0&limit=2")
    assert r1.status_code == 200
    d1 = r1.json()
    assert d1["total"] == 3
    assert len(d1["items"]) == 2

    r2 = await client.get("/api/v1/company-members/me?offset=2&limit=2")
    assert r2.status_code == 200
    d2 = r2.json()
    assert d2["total"] == 3
    assert len(d2["items"]) == 1
