from __future__ import annotations

from typing import Sequence
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFound, Forbidden
from app.models.company_join_request import (
    CompanyJoinRequest,
    CompanyJoinRequestStatusEnum,
)
from app.models.company_invitation import CompanyInvitationStatusEnum
from app.models.user import User
from app.repositories.company import CompanyRepository
from app.repositories.company_member import CompanyMemberRepository
from app.repositories.company_join_request import CompanyJoinRequestRepository
from app.repositories.company_invitation import CompanyInvitationRepository


class CompanyJoinRequestService:
    def __init__(
        self,
        company_repo: CompanyRepository | None = None,
        member_repo: CompanyMemberRepository | None = None,
        join_request_repo: CompanyJoinRequestRepository | None = None,
        invitation_repo: CompanyInvitationRepository | None = None,
    ) -> None:
        self.company_repo = company_repo or CompanyRepository()
        self.member_repo = member_repo or CompanyMemberRepository()
        self.join_request_repo = (join_request_repo
                                  or
                                  CompanyJoinRequestRepository())
        self.invitation_repo = invitation_repo or CompanyInvitationRepository()

    async def _get_company_or_404(
        self,
        db: AsyncSession,
        company_id: UUID,
    ):
        company = await self.company_repo.get_by_id(db, company_id)
        if company is None:
            raise NotFound("Company not found")
        return company

    async def create_join_request(
        self,
        db: AsyncSession,
        *,
        company_id: UUID,
        current_user: User,
    ) -> CompanyJoinRequest:
        company = await self._get_company_or_404(db, company_id)

        if company.owner_id == current_user.id:
            raise Forbidden("Owner is already part of this company")

        existing_member = await self.member_repo.get_one_for_company_and_user(
            db,
            company_id=company.id,
            user_id=current_user.id,
        )
        if existing_member is not None:
            raise Forbidden("User is already a member of this company")

        existing_request = await self.join_request_repo.get_one_by(
            db,
            company_id=company.id,
            user_id=current_user.id,
            status=CompanyJoinRequestStatusEnum.PENDING,
        )
        if existing_request is not None:
            raise Forbidden(
                "There is already a pending join request for this company"
            )

        existing_invitation = await self.invitation_repo.get_one_by(
            db,
            company_id=company.id,
            invited_user_id=current_user.id,
            status=CompanyInvitationStatusEnum.PENDING,
        )
        if existing_invitation is not None:
            raise Forbidden(
                "There is already a pending invitation from this company"
            )

        join_request = await self.join_request_repo.create_one(
            db,
            company_id=company.id,
            user_id=current_user.id,
            status=CompanyJoinRequestStatusEnum.PENDING,
        )
        return join_request

    async def cancel_join_request(
        self,
        db: AsyncSession,
        *,
        join_request_id: UUID,
        current_user: User,
    ) -> CompanyJoinRequest:
        join_request = await self.join_request_repo.get_by_id(
            db,
            join_request_id
        )
        if join_request is None:
            raise NotFound("Join request not found")

        if join_request.user_id != current_user.id:
            raise Forbidden("Only request owner can cancel this join request")

        if join_request.status != CompanyJoinRequestStatusEnum.PENDING:
            raise Forbidden("Only pending join requests can be canceled")

        updated = await self.join_request_repo.update_one(
            db,
            join_request_id,
            status=CompanyJoinRequestStatusEnum.CANCELED,
        )
        if updated is None:
            raise NotFound("Join request not found")

        return updated

    async def approve_join_request(
        self,
        db: AsyncSession,
        *,
        join_request_id: UUID,
        current_user: User,
    ) -> CompanyJoinRequest:
        join_request = await self.join_request_repo.get_by_id(
            db,
            join_request_id
        )
        if join_request is None:
            raise NotFound("Join request not found")

        company = await self._get_company_or_404(db, join_request.company_id)

        if company.owner_id != current_user.id:
            raise Forbidden("Only company owner can approve join requests")

        if join_request.status != CompanyJoinRequestStatusEnum.PENDING:
            raise Forbidden("Only pending join requests can be approved")

        user_id = join_request.user_id
        company_id = company.id

        existing_member = await self.member_repo.get_one_for_company_and_user(
            db,
            company_id=company_id,
            user_id=user_id,
        )
        if existing_member is not None:
            raise Forbidden("User is already a member of this company")

        pending_invitation = await self.invitation_repo.get_one_by(
            db,
            company_id=company_id,
            invited_user_id=user_id,
            status=CompanyInvitationStatusEnum.PENDING,
        )
        if pending_invitation is not None:
            await self.invitation_repo.update_one(
                db,
                pending_invitation.id,
                status=CompanyInvitationStatusEnum.CANCELED,
            )

        await self.member_repo.create_one(
            db,
            company_id=company_id,
            user_id=user_id,
        )

        updated = await self.join_request_repo.update_one(
            db,
            join_request_id,
            status=CompanyJoinRequestStatusEnum.APPROVED,
        )
        if updated is None:
            raise NotFound("Join request not found")

        return updated

    async def reject_join_request(
        self,
        db: AsyncSession,
        *,
        join_request_id: UUID,
        current_user: User,
    ) -> CompanyJoinRequest:
        join_request = await self.join_request_repo.get_by_id(
            db,
            join_request_id
        )
        if join_request is None:
            raise NotFound("Join request not found")

        company = await self._get_company_or_404(db, join_request.company_id)

        if company.owner_id != current_user.id:
            raise Forbidden("Only company owner can reject join requests")

        if join_request.status != CompanyJoinRequestStatusEnum.PENDING:
            raise Forbidden("Only pending join requests can be rejected")

        updated = await self.join_request_repo.update_one(
            db,
            join_request_id,
            status=CompanyJoinRequestStatusEnum.REJECTED,
        )
        if updated is None:
            raise NotFound("Join request not found")

        return updated

    async def list_my_join_requests(
        self,
        db: AsyncSession,
        *,
        current_user: User,
        status: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Sequence[CompanyJoinRequest]:
        return await self.join_request_repo.list_for_user(
            db,
            user_id=current_user.id,
            status=status,
            offset=offset,
            limit=limit,
        )

    async def list_company_join_requests(
        self,
        db: AsyncSession,
        *,
        company_id: UUID,
        current_user: User,
        status: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Sequence[CompanyJoinRequest]:
        company = await self._get_company_or_404(db, company_id)

        if company.owner_id != current_user.id:
            raise Forbidden(
                "Only company owner can view company join requests"
            )

        return await self.join_request_repo.list_for_company(
            db,
            company_id=company.id,
            status=status,
            offset=offset,
            limit=limit,
        )


join_request_service = CompanyJoinRequestService()
