from __future__ import annotations

from typing import Sequence
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFound, Forbidden
from app.models.company import Company
from app.models.user import User
from app.repositories.company import CompanyRepository
from app.repositories.company_member import CompanyMemberRepository


class CompanyMemberService:
    def __init__(
        self,
        company_repo: CompanyRepository | None = None,
        member_repo: CompanyMemberRepository | None = None,
    ) -> None:
        self.company_repo = company_repo or CompanyRepository()
        self.member_repo = member_repo or CompanyMemberRepository()

    async def _get_company_or_404(
        self,
        db: AsyncSession,
        company_id: UUID,
    ) -> Company:
        company = await self.company_repo.get_by_id(db, company_id)
        if company is None:
            raise NotFound("Company not found")
        return company

    async def remove_member_from_company(
        self,
        db: AsyncSession,
        *,
        company_id: UUID,
        member_user_id: int,
        current_user: User,
    ) -> None:

        company = await self._get_company_or_404(db, company_id)

        if company.owner_id != current_user.id:
            raise Forbidden("Only company owner can remove members")

        if member_user_id == company.owner_id:
            raise Forbidden("Owner cannot be removed from the company")

        membership = await self.member_repo.get_one_for_company_and_user(
            db,
            company_id=company.id,
            user_id=member_user_id,
        )
        if membership is None:
            raise Forbidden("User is not a member of this company")

        await self.member_repo.delete_one(db, membership.id)

    async def leave_company(
        self,
        db: AsyncSession,
        *,
        company_id: UUID,
        current_user: User,
    ) -> None:

        company = await self._get_company_or_404(db, company_id)

        if company.owner_id == current_user.id:
            raise Forbidden("Owner cannot leave the company")

        membership = await self.member_repo.get_one_for_company_and_user(
            db,
            company_id=company.id,
            user_id=current_user.id,
        )
        if membership is None:
            raise Forbidden("User is not a member of this company")

        await self.member_repo.delete_one(db, membership.id)

    async def list_company_members(
        self,
        db: AsyncSession,
        *,
        company_id: UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> Sequence[User]:

        await self._get_company_or_404(db, company_id)

        users = await self.member_repo.list_members_for_company(
            db,
            company_id=company_id,
            offset=offset,
            limit=limit,
        )
        return users


member_service = CompanyMemberService()
