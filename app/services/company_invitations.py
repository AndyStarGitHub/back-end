from __future__ import annotations

from typing import Sequence
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFound, Forbidden
from app.models.company import Company
from app.models.company_invitation import (
    CompanyInvitation,
    CompanyInvitationStatusEnum,
)
from app.models.company_join_request import CompanyJoinRequestStatusEnum
from app.models.user import User
from app.repositories.company import CompanyRepository
from app.repositories.company_invitation import CompanyInvitationRepository
from app.repositories.company_member import CompanyMemberRepository
from app.repositories.company_join_request import CompanyJoinRequestRepository
from app.repositories.user_repo import UserRepository


class CompanyInvitationService:
    def __init__(
        self,
        invitation_repo: CompanyInvitationRepository | None = None,
        company_repo: CompanyRepository | None = None,
        member_repo: CompanyMemberRepository | None = None,
        join_request_repo: CompanyJoinRequestRepository | None = None,
        user_repo: UserRepository | None = None,
    ) -> None:
        self.invitation_repo = invitation_repo or CompanyInvitationRepository()
        self.company_repo = company_repo or CompanyRepository()
        self.member_repo = member_repo or CompanyMemberRepository()
        self.join_request_repo = (join_request_repo
                                  or
                                  CompanyJoinRequestRepository())
        self.user_repo = user_repo or UserRepository()

    async def _get_company_or_404(
        self,
        db: AsyncSession,
        company_id: UUID,
    ) -> Company:
        company = await self.company_repo.get_by_id(db, company_id)
        if company is None:
            raise NotFound("Company not found")
        return company

    async def _get_invitation_or_404(
        self,
        db: AsyncSession,
        invitation_id: UUID,
    ) -> CompanyInvitation:
        invitation = await self.invitation_repo.get_by_id(db, invitation_id)
        if invitation is None:
            raise NotFound("Invitation not found")
        return invitation

    async def invite_user_to_company(
        self,
        db: AsyncSession,
        *,
        company_id: UUID,
        invited_user_id: int,
        current_user: User,
    ) -> CompanyInvitation:
        company = await self._get_company_or_404(db, company_id)

        if company.owner_id != current_user.id:
            raise Forbidden("Only company owner can invite users")

        if invited_user_id == current_user.id:
            raise Forbidden("Owner cannot invite himself")

        invited_user = await self._get_user_or_404(db, invited_user_id)

        existing_member = await self.member_repo.get_one_by(
            db,
            company_id=company.id,
            user_id=invited_user.id,
        )
        if existing_member is not None:
            raise Forbidden("User is already a member of this company")

        existing_invitation = await self.invitation_repo.get_pending_for_company_and_user(
            db,
            company_id=company.id,
            invited_user_id=invited_user.id,
        )
        if existing_invitation is not None:
            raise Forbidden(
                "There is already a pending invitation for this user"
            )

        existing_join_request = await self.join_request_repo.get_one_by(
            db,
            company_id=company.id,
            user_id=invited_user.id,
            status=CompanyJoinRequestStatusEnum.PENDING,
        )
        if existing_join_request is not None:
            raise Forbidden(
                "User already has a pending join request for this company"
            )

        invitation = await self.invitation_repo.create_one(
            db,
            company_id=company.id,
            invited_user_id=invited_user.id,
            invited_by_id=current_user.id,
            status=CompanyInvitationStatusEnum.PENDING,
        )

        return invitation

    async def _get_user_or_404(
            self,
            db: AsyncSession,
            user_id: int,
    ) -> User:
        user = await self.user_repo.get_by_id(db, user_id)
        if user is None:
            raise NotFound("Invited user not found")
        return user

    async def cancel_invitation(
        self,
        db: AsyncSession,
        *,
        invitation_id: UUID,
        current_user: User,
    ) -> CompanyInvitation:
        invitation = await self._get_invitation_or_404(db, invitation_id)
        company = invitation.company

        if company.owner_id != current_user.id:
            raise Forbidden("Only company owner can cancel invitations")

        if invitation.status != CompanyInvitationStatusEnum.PENDING:
            raise Forbidden("Only pending invitations can be canceled")

        updated = await self.invitation_repo.update_one(
            db,
            invitation_id,
            status=CompanyInvitationStatusEnum.CANCELED,
        )

        if updated is None:
            raise NotFound("Invitation not found")

        return updated

    async def accept_invitation(
        self,
        db: AsyncSession,
        *,
        invitation_id: UUID,
        current_user: User,
    ) -> CompanyInvitation:
        invitation = await self._get_invitation_or_404(db, invitation_id)

        if invitation.invited_user_id != current_user.id:
            raise Forbidden("Only invited user can accept this invitation")

        if invitation.status != CompanyInvitationStatusEnum.PENDING:
            raise Forbidden("Only pending invitations can be accepted")

        company_id = invitation.company_id

        existing_member = await self.member_repo.get_one_by(
            db,
            company_id=company_id,
            user_id=current_user.id,
        )
        if existing_member is not None:
            raise Forbidden("User is already a member of this company")

        existing_join_request = await self.join_request_repo.get_one_by(
            db,
            company_id=company_id,
            user_id=current_user.id,
            status=CompanyJoinRequestStatusEnum.PENDING,
        )
        if existing_join_request is not None:
            await self.join_request_repo.update_one(
                db,
                existing_join_request.id,
                status=CompanyJoinRequestStatusEnum.CANCELED,
            )

        await self.member_repo.create_one(
            db,
            company_id=company_id,
            user_id=current_user.id,
        )

        updated = await self.invitation_repo.update_one(
            db,
            invitation.id,
            status=CompanyInvitationStatusEnum.ACCEPTED,
        )
        if updated is None:
            raise NotFound("Invitation not found")

        return updated

    async def decline_invitation(
        self,
        db: AsyncSession,
        *,
        invitation_id: UUID,
        current_user: User,
    ) -> CompanyInvitation:
        invitation = await self._get_invitation_or_404(db, invitation_id)

        if invitation.invited_user_id != current_user.id:
            raise Forbidden("Only invited user can decline this invitation")

        if invitation.status != CompanyInvitationStatusEnum.PENDING:
            raise Forbidden("Only pending invitations can be declined")

        updated = await self.invitation_repo.update_one(
            db,
            invitation.id,
            status=CompanyInvitationStatusEnum.DECLINED,
        )
        if updated is None:
            raise NotFound("Invitation not found")

        return updated

    async def list_my_invitations(
        self,
        db: AsyncSession,
        *,
        current_user: User,
        status: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Sequence[CompanyInvitation]:

        status_enum: CompanyInvitationStatusEnum | None = None
        if status is not None:
            try:
                status_enum = CompanyInvitationStatusEnum(status)
            except ValueError:
                return []

        invitations = await self.invitation_repo.list_for_user(
            db,
            user_id=current_user.id,
            status=status_enum,
            offset=offset,
            limit=limit,
        )
        return invitations

    async def list_company_invitations(
        self,
        db: AsyncSession,
        *,
        company_id: UUID,
        current_user: User,
        status: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Sequence[CompanyInvitation]:
        company = await self._get_company_or_404(db, company_id)

        if company.owner_id != current_user.id:
            raise Forbidden("Only company owner can view company invitations")

        status_enum: CompanyInvitationStatusEnum | None = None
        if status is not None:
            try:
                status_enum = CompanyInvitationStatusEnum(status)
            except ValueError:
                return []

        invitations = await self.invitation_repo.list_for_company(
            db,
            company_id=company.id,
            status=status_enum,
            offset=offset,
            limit=limit,
        )
        return invitations


invitation_service = CompanyInvitationService()
