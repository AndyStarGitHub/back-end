import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import Forbidden
from app.models.company_join_request import CompanyJoinRequestStatusEnum
from app.services.company_join_requests import join_request_service

pytestmark = pytest.mark.anyio


async def test_owner_can_reject_pending_join_request(
    db_session: AsyncSession,
    user_factory,
    company_factory,
):
    owner = await user_factory(email="owner@example.com")
    requester = await user_factory(email="requester@example.com")
    company = await company_factory(owner=owner)

    jr = await join_request_service.create_join_request(
        db=db_session,
        company_id=company.id,
        current_user=requester,
    )
    assert jr.status == CompanyJoinRequestStatusEnum.PENDING.value

    rejected = await join_request_service.reject_join_request(
        db=db_session,
        join_request_id=jr.id,
        current_user=owner,
    )

    assert rejected.id == jr.id
    assert rejected.status == CompanyJoinRequestStatusEnum.REJECTED.value


async def test_user_can_cancel_own_pending_join_request(
    db_session: AsyncSession,
    user_factory,
    company_factory,
):
    owner = await user_factory(email="owner@example.com")
    requester = await user_factory(email="requester@example.com")
    company = await company_factory(owner=owner)

    jr = await join_request_service.create_join_request(
        db=db_session,
        company_id=company.id,
        current_user=requester,
    )
    assert jr.status == CompanyJoinRequestStatusEnum.PENDING.value

    canceled = await join_request_service.cancel_join_request(
        db=db_session,
        join_request_id=jr.id,
        current_user=requester,
    )

    assert canceled.id == jr.id
    assert canceled.status == CompanyJoinRequestStatusEnum.CANCELED.value


async def test_list_my_join_requests_invalid_status_returns_empty(
    db_session: AsyncSession,
    user_factory,
    company_factory,
):
    owner = await user_factory(email="owner@example.com")
    requester = await user_factory(email="requester@example.com")
    company = await company_factory(owner=owner)

    await join_request_service.create_join_request(
        db=db_session,
        company_id=company.id,
        current_user=requester,
    )

    res = await join_request_service.list_my_join_requests(
        db=db_session,
        current_user=requester,
        status="NOT_A_REAL_STATUS",
        limit=20,
        offset=0,
    )

    assert res == []


async def test_non_owner_cannot_list_company_join_requests(
    db_session: AsyncSession,
    user_factory,
    company_factory,
):
    owner = await user_factory(email="owner@example.com")
    other = await user_factory(email="other@example.com")
    requester = await user_factory(email="requester@example.com")
    company = await company_factory(owner=owner)

    await join_request_service.create_join_request(
        db=db_session,
        company_id=company.id,
        current_user=requester,
    )

    with pytest.raises(Forbidden):
        await join_request_service.list_company_join_requests(
            db=db_session,
            company_id=company.id,
            current_user=other,
            limit=20,
            offset=0,
        )
