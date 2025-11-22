from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFound, Forbidden
from app.models.company import Company
from app.models.company_member import CompanyMember
from app.models.company_invitation import (
    CompanyInvitation,
    CompanyInvitationStatusEnum,
)
from app.models.company_join_request import (
    CompanyJoinRequest,
    CompanyJoinRequestStatusEnum,
)
from app.models.user import User


async def create_join_request(
    db: AsyncSession,
    company_id: str,
    current_user: User,
) -> CompanyJoinRequest:

    result = await db.execute(
        select(Company).where(Company.id == company_id)
    )
    company: Company | None = result.scalar_one_or_none()
    if company is None:
        raise NotFound("Company not found")

    if company.owner_id == current_user.id:
        raise Forbidden("Owner is already part of this company")

    result = await db.execute(
        select(CompanyMember).where(
            CompanyMember.company_id == company.id,
            CompanyMember.user_id == current_user.id,
        )
    )
    existing_member: CompanyMember | None = result.scalar_one_or_none()
    if existing_member is not None:
        raise Forbidden("User is already a member of this company")

    result = await db.execute(
        select(CompanyJoinRequest).where(
            CompanyJoinRequest.company_id == company.id,
            CompanyJoinRequest.user_id == current_user.id,
            CompanyJoinRequest.status == CompanyJoinRequestStatusEnum.PENDING,
        )
    )
    existing_request: CompanyJoinRequest | None = result.scalar_one_or_none()
    if existing_request is not None:
        raise Forbidden(
            "There is already a pending join request for this company"
        )

    result = await db.execute(
        select(CompanyInvitation).where(
            CompanyInvitation.company_id == company.id,
            CompanyInvitation.invited_user_id == current_user.id,
            CompanyInvitation.status == CompanyInvitationStatusEnum.PENDING,
        )
    )
    existing_invitation: CompanyInvitation | None = result.scalar_one_or_none()
    if existing_invitation is not None:
        raise Forbidden(
            "There is already a pending invitation from this company"
        )

    join_request = CompanyJoinRequest(
        company_id=company.id,
        user_id=current_user.id,
        status=CompanyJoinRequestStatusEnum.PENDING,
    )

    db.add(join_request)
    await db.commit()
    await db.refresh(join_request)

    return join_request


async def cancel_join_request(
    db: AsyncSession,
    join_request_id: str,
    current_user: User,
) -> CompanyJoinRequest:

    result = await db.execute(
        select(CompanyJoinRequest).where(
            CompanyJoinRequest.id == join_request_id
        )
    )
    join_request: CompanyJoinRequest | None = result.scalar_one_or_none()
    if join_request is None:
        raise NotFound("Join request not found")

    if join_request.user_id != current_user.id:
        raise Forbidden("Only request owner can cancel this join request")

    if join_request.status != CompanyJoinRequestStatusEnum.PENDING:
        raise Forbidden("Only pending join requests can be canceled")

    join_request.status = CompanyJoinRequestStatusEnum.CANCELED

    db.add(join_request)
    await db.commit()
    await db.refresh(join_request)

    return join_request


async def approve_join_request(
    db: AsyncSession,
    join_request_id: str,
    current_user: User,
) -> CompanyJoinRequest:

    result = await db.execute(
        select(CompanyJoinRequest).where(
            CompanyJoinRequest.id == join_request_id
        )
    )
    join_request: CompanyJoinRequest | None = result.scalar_one_or_none()
    if join_request is None:
        raise NotFound("Join request not found")

    company_id = join_request.company_id

    result = await db.execute(
        select(Company).where(Company.id == company_id)
    )
    company: Company | None = result.scalar_one_or_none()
    if company is None:
        raise NotFound("Company not found")

    if company.owner_id != current_user.id:
        raise Forbidden("Only company owner can approve join requests")

    if join_request.status != CompanyJoinRequestStatusEnum.PENDING:
        raise Forbidden("Only pending join requests can be approved")

    user_id = join_request.user_id

    result = await db.execute(
        select(CompanyMember).where(
            CompanyMember.company_id == company_id,
            CompanyMember.user_id == user_id,
        )
    )
    existing_member: CompanyMember | None = result.scalar_one_or_none()
    if existing_member is not None:
        raise Forbidden("User is already a member of this company")

    result = await db.execute(
        select(CompanyInvitation).where(
            CompanyInvitation.company_id == company_id,
            CompanyInvitation.invited_user_id == user_id,
            CompanyInvitation.status == CompanyInvitationStatusEnum.PENDING,
        )
    )
    pending_invitation: CompanyInvitation | None = result.scalar_one_or_none()
    if pending_invitation is not None:
        pending_invitation.status = CompanyInvitationStatusEnum.CANCELED
        db.add(pending_invitation)

    membership = CompanyMember(
        company_id=company_id,
        user_id=user_id,
    )
    db.add(membership)

    join_request.status = CompanyJoinRequestStatusEnum.APPROVED
    db.add(join_request)

    await db.commit()
    await db.refresh(join_request)

    return join_request


async def reject_join_request(
    db: AsyncSession,
    join_request_id: str,
    current_user: User,
) -> CompanyJoinRequest:

    result = await db.execute(
        select(CompanyJoinRequest).where(
            CompanyJoinRequest.id == join_request_id
        )
    )
    join_request: CompanyJoinRequest | None = result.scalar_one_or_none()
    if join_request is None:
        raise NotFound("Join request not found")

    company_id = join_request.company_id

    result = await db.execute(
        select(Company).where(Company.id == company_id)
    )
    company: Company | None = result.scalar_one_or_none()
    if company is None:
        raise NotFound("Company not found")

    if company.owner_id != current_user.id:
        raise Forbidden("Only company owner can reject join requests")

    if join_request.status != CompanyJoinRequestStatusEnum.PENDING:
        raise Forbidden("Only pending join requests can be rejected")

    join_request.status = CompanyJoinRequestStatusEnum.REJECTED

    db.add(join_request)
    await db.commit()
    await db.refresh(join_request)

    return join_request


async def list_my_join_requests(
    db: AsyncSession,
    current_user: User,
    status: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> Sequence[CompanyJoinRequest]:

    stmt = select(CompanyJoinRequest).where(
        CompanyJoinRequest.user_id == current_user.id
    )

    if status is not None:
        stmt = stmt.where(CompanyJoinRequest.status == status)

    stmt = (
        stmt.order_by(CompanyJoinRequest.created_at.desc())
        .offset(offset)
        .limit(limit)
    )

    result = await db.execute(stmt)
    join_requests = result.scalars().all()
    return join_requests


async def list_company_join_requests(
    db: AsyncSession,
    company_id: str,
    current_user: User,
    status: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> Sequence[CompanyJoinRequest]:

    result = await db.execute(
        select(Company).where(Company.id == company_id)
    )
    company: Company | None = result.scalar_one_or_none()
    if company is None:
        raise NotFound("Company not found")

    if company.owner_id != current_user.id:
        raise Forbidden("Only company owner can view company join requests")

    stmt = select(CompanyJoinRequest).where(
        CompanyJoinRequest.company_id == company.id
    )

    if status is not None:
        stmt = stmt.where(CompanyJoinRequest.status == status)

    stmt = (
        stmt.order_by(CompanyJoinRequest.created_at.desc())
        .offset(offset)
        .limit(limit)
    )

    result = await db.execute(stmt)
    join_requests = result.scalars().all()
    return join_requests
