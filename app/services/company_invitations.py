from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import Forbidden, NotFound
from app.models.company import Company
from app.models.company_member import CompanyMember
from app.models.company_invitation import CompanyInvitation, CompanyInvitationStatusEnum
from app.models.company_join_request import (
    CompanyJoinRequest,
    CompanyJoinRequestStatusEnum,
)
from app.models.user import User


async def invite_user_to_company(
    db: AsyncSession,
    company_id: str,
    invited_user_id: int,
    current_user: User,
) -> CompanyInvitation:

    result = await db.execute(
        select(Company).where(Company.id == company_id)
    )
    company: Company | None = result.scalar_one_or_none()
    if company is None:
        raise NotFound("Company not found")

    if company.owner_id != current_user.id:
        raise Forbidden("Only company owner can invite users")

    if invited_user_id == current_user.id:
        raise Forbidden("Owner cannot invite himself")

    result = await db.execute(
        select(User).where(User.id == invited_user_id)
    )
    invited_user: User | None = result.scalar_one_or_none()
    if invited_user is None:
        raise NotFound("Invited user not found")

    result = await db.execute(
        select(CompanyMember).where(
            CompanyMember.company_id == company.id,
            CompanyMember.user_id == invited_user_id,
        )
    )
    existing_member: CompanyMember | None = result.scalar_one_or_none()
    if existing_member is not None:
        raise Forbidden("User is already a member of this company")

    result = await db.execute(
        select(CompanyInvitation).where(
            CompanyInvitation.company_id == company.id,
            CompanyInvitation.invited_user_id == invited_user_id,
            CompanyInvitation.status == CompanyInvitationStatusEnum.PENDING.value,
        )
    )
    existing_invitation: CompanyInvitation | None = result.scalar_one_or_none()
    if existing_invitation is not None:
        raise Forbidden("There is already a pending invitation for this user")

    result = await db.execute(
        select(CompanyJoinRequest).where(
            CompanyJoinRequest.company_id == company.id,
            CompanyJoinRequest.user_id == invited_user_id,
            CompanyJoinRequest.status == CompanyJoinRequestStatusEnum.PENDING.value,
        )
    )
    existing_join_request: CompanyJoinRequest | None = result.scalar_one_or_none()
    if existing_join_request is not None:
        raise Forbidden("User already has a pending join request for this company")

    invitation = CompanyInvitation(
        company_id=company.id,
        invited_user_id=invited_user_id,
        invited_by_id=current_user.id,
        status=CompanyInvitationStatusEnum.PENDING.value,
    )

    db.add(invitation)
    await db.commit()
    await db.refresh(invitation)

    return invitation


async def cancel_invitation(
    db: AsyncSession,
    invitation_id: str,
    current_user: User,
) -> CompanyInvitation:

    result = await db.execute(
        select(CompanyInvitation).where(CompanyInvitation.id == invitation_id)
    )
    invitation: CompanyInvitation | None = result.scalar_one_or_none()
    if invitation is None:
        raise NotFound("Invitation not found")

    result = await db.execute(
        select(Company).where(Company.id == invitation.company_id)
    )
    company: Company | None = result.scalar_one_or_none()
    if company is None:
        raise NotFound("Company not found")

    if company.owner_id != current_user.id:
        raise Forbidden("Only company owner can cancel invitations")

    if invitation.status != CompanyInvitationStatusEnum.PENDING.value:
        raise Forbidden("Only pending invitations can be canceled")

    invitation.status = CompanyInvitationStatusEnum.CANCELED.value

    db.add(invitation)
    await db.commit()
    await db.refresh(invitation)

    return invitation


async def accept_invitation(
    db: AsyncSession,
    invitation_id: str,
    current_user: User,
) -> CompanyInvitation:

    result = await db.execute(
        select(CompanyInvitation).where(CompanyInvitation.id == invitation_id)
    )
    invitation: CompanyInvitation | None = result.scalar_one_or_none()
    if invitation is None:
        raise NotFound("Invitation not found")

    if invitation.invited_user_id != current_user.id:
        raise Forbidden("Only invited user can accept this invitation")

    if invitation.status != CompanyInvitationStatusEnum.PENDING.value:
        raise Forbidden("Only pending invitations can be accepted")

    company_id = invitation.company_id

    result = await db.execute(
        select(CompanyMember).where(
            CompanyMember.company_id == company_id,
            CompanyMember.user_id == current_user.id,
        )
    )
    existing_member: CompanyMember | None = result.scalar_one_or_none()
    if existing_member is not None:
        raise Forbidden("User is already a member of this company")

    result = await db.execute(
        select(CompanyJoinRequest).where(
            CompanyJoinRequest.company_id == company_id,
            CompanyJoinRequest.user_id == current_user.id,
            CompanyJoinRequest.status == CompanyJoinRequestStatusEnum.PENDING.value,
        )
    )
    existing_join_request: CompanyJoinRequest | None = result.scalar_one_or_none()
    if existing_join_request is not None:
        existing_join_request.status = CompanyJoinRequestStatusEnum.CANCELED.value
        db.add(existing_join_request)

    membership = CompanyMember(
        company_id=company_id,
        user_id=current_user.id,
    )
    db.add(membership)

    invitation.status = CompanyInvitationStatusEnum.ACCEPTED.value
    db.add(invitation)

    await db.commit()
    await db.refresh(invitation)

    return invitation


async def decline_invitation(
    db: AsyncSession,
    invitation_id: str,
    current_user: User,
) -> CompanyInvitation:

    result = await db.execute(
        select(CompanyInvitation).where(CompanyInvitation.id == invitation_id)
    )
    invitation: CompanyInvitation | None = result.scalar_one_or_none()
    if invitation is None:
        raise NotFound("Invitation not found")

    if invitation.invited_user_id != current_user.id:
        raise Forbidden("Only invited user can decline this invitation")

    if invitation.status != CompanyInvitationStatusEnum.PENDING.value:
        raise Forbidden("Only pending invitations can be declined")

    invitation.status = CompanyInvitationStatusEnum.DECLINED.value

    db.add(invitation)
    await db.commit()
    await db.refresh(invitation)

    return invitation


async def list_my_invitations(
    db: AsyncSession,
    current_user: User,
    status: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> Sequence[CompanyInvitation]:

    stmt = select(CompanyInvitation).where(
        CompanyInvitation.invited_user_id == current_user.id
    )

    if status is not None:
        stmt = stmt.where(CompanyInvitation.status == status)

    stmt = (
        stmt.order_by(CompanyInvitation.created_at.desc())
        .offset(offset)
        .limit(limit)
    )

    result = await db.execute(stmt)
    invitations = result.scalars().all()
    return invitations


async def list_company_invitations(
    db: AsyncSession,
    company_id: str,
    current_user: User,
    status: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> Sequence[CompanyInvitation]:

    result = await db.execute(
        select(Company).where(Company.id == company_id)
    )
    company: Company | None = result.scalar_one_or_none()
    if company is None:
        raise NotFound("Company not found")

    if company.owner_id != current_user.id:
        raise Forbidden("Only company owner can view company invitations")

    stmt = select(CompanyInvitation).where(
        CompanyInvitation.company_id == company.id
    )

    if status is not None:
        stmt = stmt.where(CompanyInvitation.status == status)

    stmt = (
        stmt.order_by(CompanyInvitation.created_at.desc())
        .offset(offset)
        .limit(limit)
    )

    result = await db.execute(stmt)
    invitations = result.scalars().all()
    return invitations
