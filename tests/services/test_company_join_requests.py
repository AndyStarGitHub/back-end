import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import Forbidden
from app.models.company_join_request import CompanyJoinRequestStatusEnum
from app.models.company_member import CompanyMember
from app.services.company_join_requests import (
    create_join_request,
    approve_join_request,
)


pytestmark = pytest.mark.anyio


async def test_user_can_create_join_request(
    db_session: AsyncSession,
    user_factory,
    company_factory,
):
    owner = await user_factory(email="owner@example.com")
    user = await user_factory(email="user@example.com")
    company = await company_factory(owner=owner)

    join_request = await create_join_request(
        db=db_session,
        company_id=company.id,
        current_user=user,
    )

    assert join_request.company_id == company.id
    assert join_request.user_id == user.id
    assert join_request.status == CompanyJoinRequestStatusEnum.PENDING.value


async def test_owner_cannot_create_join_request_for_own_company(
    db_session: AsyncSession,
    user_factory,
    company_factory,
):
    owner = await user_factory(email="owner@example.com")
    company = await company_factory(owner=owner)

    with pytest.raises(Forbidden):
        await create_join_request(
            db=db_session,
            company_id=company.id,
            current_user=owner,
        )


async def test_cannot_create_duplicate_pending_join_request(
    db_session: AsyncSession,
    user_factory,
    company_factory,
):
    owner = await user_factory(email="owner@example.com")
    user = await user_factory(email="user@example.com")
    company = await company_factory(owner=owner)

    await create_join_request(
        db=db_session,
        company_id=company.id,
        current_user=user,
    )

    with pytest.raises(Forbidden):
        await create_join_request(
            db=db_session,
            company_id=company.id,
            current_user=user,
        )


async def test_owner_can_approve_join_request_and_member_is_created(
    db_session: AsyncSession,
    user_factory,
    company_factory,
):
    owner = await user_factory(email="owner@example.com")
    user = await user_factory(email="user@example.com")
    company = await company_factory(owner=owner)

    join_request = await create_join_request(
        db=db_session,
        company_id=company.id,
        current_user=user,
    )

    approved = await approve_join_request(
        db=db_session,
        join_request_id=join_request.id,  # <-- важливо
        current_user=owner,
    )

    assert approved.status == CompanyJoinRequestStatusEnum.APPROVED.value

    result = await db_session.execute(
        CompanyMember.__table__.select().where(
            CompanyMember.company_id == company.id,
            CompanyMember.user_id == user.id,
        )
    )
    row = result.first()
    assert row is not None
