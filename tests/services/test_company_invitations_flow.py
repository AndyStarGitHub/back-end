import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company_member import CompanyMember
from app.models.company_join_request import (
    CompanyJoinRequest,
    CompanyJoinRequestStatusEnum
)
from app.models.company_invitation import CompanyInvitationStatusEnum
from app.services.company_invitations import invitation_service
from app.services.company_join_requests import join_request_service
from app.core.errors import Forbidden

pytestmark = pytest.mark.anyio


async def test_invited_user_can_accept_invitation_creates_membership(
    db_session: AsyncSession,
    user_factory,
    company_factory,
):
    owner = await user_factory(email="owner@example.com")
    invited = await user_factory(email="invited@example.com")
    company = await company_factory(owner=owner)

    inv = await invitation_service.invite_user_to_company(
        db=db_session,
        company_id=company.id,
        invited_user_id=invited.id,
        current_user=owner,
    )

    accepted = await invitation_service.accept_invitation(
        db=db_session,
        invitation_id=inv.id,
        current_user=invited,
    )

    assert accepted.status == CompanyInvitationStatusEnum.ACCEPTED.value

    member = (await db_session.execute(
        select(CompanyMember).where(
            CompanyMember.company_id == company.id,
            CompanyMember.user_id == invited.id,
        )
    )).scalar_one()
    assert member.company_id == company.id
    assert member.user_id == invited.id


async def test_non_invited_user_cannot_accept_invitation(
        db_session,
        user_factory,
        company_factory
):
    owner = await user_factory(email="owner@example.com")
    invited = await user_factory(email="invited@example.com")
    stranger = await user_factory(email="stranger@example.com")
    company = await company_factory(owner=owner)

    inv = await invitation_service.invite_user_to_company(
        db=db_session,
        company_id=company.id,
        invited_user_id=invited.id,
        current_user=owner,
    )

    with pytest.raises(Forbidden):
        await invitation_service.accept_invitation(
            db=db_session,
            invitation_id=inv.id,
            current_user=stranger,
        )


async def test_invited_user_can_decline_pending_invitation(
        db_session,
        user_factory,
        company_factory
):
    owner = await user_factory(email="owner@example.com")
    invited = await user_factory(email="invited@example.com")
    company = await company_factory(owner=owner)

    inv = await invitation_service.invite_user_to_company(
        db=db_session,
        company_id=company.id,
        invited_user_id=invited.id,
        current_user=owner,
    )

    declined = await invitation_service.decline_invitation(
        db=db_session,
        invitation_id=inv.id,
        current_user=invited,
    )

    assert declined.status == CompanyInvitationStatusEnum.DECLINED.value


async def test_owner_can_cancel_pending_invitation(
        db_session,
        user_factory,
        company_factory
):
    owner = await user_factory(email="owner@example.com")
    invited = await user_factory(email="invited@example.com")
    company = await company_factory(owner=owner)

    inv = await invitation_service.invite_user_to_company(
        db=db_session,
        company_id=company.id,
        invited_user_id=invited.id,
        current_user=owner,
    )

    canceled = await invitation_service.cancel_invitation(
        db=db_session,
        invitation_id=inv.id,
        current_user=owner,
    )
    assert canceled.status == CompanyInvitationStatusEnum.CANCELED.value


async def test_list_my_invitations_invalid_status_returns_empty(
        db_session,
        user_factory
):
    user = await user_factory(email="u@example.com")

    res = await invitation_service.list_my_invitations(
        db=db_session,
        current_user=user,
        status="NOT_A_REAL_STATUS",
        limit=20,
        offset=0,
    )
    assert res == []


async def test_non_owner_cannot_list_company_invitations(
        db_session,
        user_factory,
        company_factory
):
    owner = await user_factory(email="owner@example.com")
    other = await user_factory(email="other@example.com")
    company = await company_factory(owner=owner)

    with pytest.raises(Forbidden):
        await invitation_service.list_company_invitations(
            db=db_session,
            company_id=company.id,
            current_user=other,
        )


async def test_accept_invitation_cancels_pending_join_request_if_exists_in_db(
    db_session: AsyncSession,
    user_factory,
    company_factory,
):
    owner = await user_factory(email="owner@example.com")
    invited = await user_factory(email="invited@example.com")
    company = await company_factory(owner=owner)

    inv = await invitation_service.invite_user_to_company(
        db=db_session,
        company_id=company.id,
        invited_user_id=invited.id,
        current_user=owner,
    )

    jr = CompanyJoinRequest(
        company_id=company.id,
        user_id=invited.id,
        status=CompanyJoinRequestStatusEnum.PENDING.value,
    )
    db_session.add(jr)
    await db_session.commit()
    await db_session.refresh(jr)

    accepted = await invitation_service.accept_invitation(
        db=db_session,
        invitation_id=inv.id,
        current_user=invited,
    )
    assert accepted.status == CompanyInvitationStatusEnum.ACCEPTED.value

    jr_db = (await db_session.execute(
        select(CompanyJoinRequest).where(CompanyJoinRequest.id == jr.id)
    )).scalar_one()
    assert jr_db.status == CompanyJoinRequestStatusEnum.CANCELED.value


async def test_cannot_invite_user_with_pending_join_request(
    db_session: AsyncSession,
    user_factory,
    company_factory,
):
    owner = await user_factory(email="owner@example.com")
    invited = await user_factory(email="invited@example.com")
    company = await company_factory(owner=owner)

    await join_request_service.create_join_request(
        db=db_session,
        company_id=company.id,
        current_user=invited,
    )

    with pytest.raises(Forbidden):
        await invitation_service.invite_user_to_company(
            db=db_session,
            company_id=company.id,
            invited_user_id=invited.id,
            current_user=owner,
        )
