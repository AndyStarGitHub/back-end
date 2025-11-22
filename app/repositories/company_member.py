from __future__ import annotations

from typing import Sequence, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company_member import CompanyMember, CompanyMemberRoleEnum
from app.models.user import User
from app.repositories.base import BaseRepository


class CompanyMemberRepository(BaseRepository[CompanyMember]):
    def __init__(self) -> None:
        super().__init__(CompanyMember)

    async def get_one_for_company_and_user(
        self,
        db: AsyncSession,
        *,
        company_id: Any,
        user_id: int,
    ) -> CompanyMember | None:
        return await self.get_one_by(
            db,
            company_id=company_id,
            user_id=user_id,
        )

    async def list_members_for_company(
        self,
        db: AsyncSession,
        *,
        company_id: Any,
        offset: int = 0,
        limit: int = 20,
    ) -> Sequence[User]:
        stmt = (
            select(User)
            .join(CompanyMember, CompanyMember.user_id == User.id)
            .where(CompanyMember.company_id == company_id)
            .order_by(User.id)
            .offset(offset)
            .limit(limit)
        )
        res = await db.execute(stmt)
        return res.scalars().all()

    async def list_admins_for_company(
        self,
        db: AsyncSession,
        *,
        company_id: Any,
    ) -> Sequence[User]:
        stmt = (
            select(User)
            .join(CompanyMember, CompanyMember.user_id == User.id)
            .where(
                CompanyMember.company_id == company_id,
                CompanyMember.role == CompanyMemberRoleEnum.ADMIN,
            )
            .order_by(User.id)
        )
        res = await db.execute(stmt)
        return res.scalars().all()
