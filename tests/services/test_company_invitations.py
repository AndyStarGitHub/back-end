import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import Forbidden
from app.models.company_invitation import CompanyInvitationStatusEnum
from app.models.company_member import CompanyMember
from app.services.company_invitations import invitation_service


pytestmark = pytest.mark.anyio


async def test_owner_can_invite_user(
    db_session: AsyncSession,
    user_factory,
    company_factory,
):
    owner = await user_factory(email="owner@example.com")
    invited = await user_factory(email="invited@example.com")
    company = await company_factory(owner=owner)

    invitation = await invitation_service.invite_user_to_company(
        db=db_session,
        company_id=company.id,
        invited_user_id=invited.id,
        current_user=owner,
    )

    assert invitation.company_id == company.id
    assert invitation.invited_user_id == invited.id
    assert invitation.status == CompanyInvitationStatusEnum.PENDING.value


async def test_non_owner_cannot_invite_user(
    db_session: AsyncSession,
    user_factory,
    company_factory,
):
    owner = await user_factory(email="owner@example.com")
    other = await user_factory(email="other@example.com")
    invited = await user_factory(email="invited@example.com")
    company = await company_factory(owner=owner)

    with pytest.raises(Forbidden):
        await invitation_service.invite_user_to_company(
            db=db_session,
            company_id=company.id,
            invited_user_id=invited.id,
            current_user=other,
        )


async def test_cannot_invite_existing_member(
    db_session: AsyncSession,
    user_factory,
    company_factory,
):
    owner = await user_factory(email="owner@example.com")
    member = await user_factory(email="member@example.com")
    company = await company_factory(owner=owner)

    membership = CompanyMember(company_id=company.id, user_id=member.id)
    db_session.add(membership)
    await db_session.commit()

    with pytest.raises(Forbidden):
        await invitation_service.invite_user_to_company(
            db=db_session,
            company_id=company.id,
            invited_user_id=member.id,
            current_user=owner,
        )


async def test_cannot_create_duplicate_pending_invitation(
    db_session: AsyncSession,
    user_factory,
    company_factory,
):
    owner = await user_factory(email="owner@example.com")
    invited = await user_factory(email="invited@example.com")
    company = await company_factory(owner=owner)

    await invitation_service.invite_user_to_company(
        db=db_session,
        company_id=company.id,
        invited_user_id=invited.id,
        current_user=owner,
    )

    with pytest.raises(Forbidden):
        await invitation_service.invite_user_to_company(
            db=db_session,
            company_id=company.id,
            invited_user_id=invited.id,
            current_user=owner,
        )
