from __future__ import annotations

from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.company_invitation import (
    CompanyInvitation,
    CompanyInvitationStatusEnum,
)
from app.repositories.base import BaseRepository


class CompanyInvitationRepository(BaseRepository[CompanyInvitation]):
    def __init__(self) -> None:
        super().__init__(CompanyInvitation)

    async def get_pending_for_company_and_user(
        self,
        db: AsyncSession,
        *,
        company_id,
        invited_user_id: int,
    ) -> CompanyInvitation | None:
        stmt = (select(self.model)
            .options(selectinload(self.model.company))
            .where(
            self.model.company_id == company_id,
            self.model.invited_user_id == invited_user_id,
            self.model.status == CompanyInvitationStatusEnum.PENDING,
        ))
        res = await db.execute(stmt)
        return res.scalars().first()

    async def list_for_user(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        status: CompanyInvitationStatusEnum | None,
        offset: int = 0,
        limit: int = 20,
    ) -> Sequence[CompanyInvitation]:
        stmt = (select(self.model)
            .options(selectinload(self.model.company))
            .where(
            self.model.invited_user_id == user_id,
        ))
        if status is not None:
            stmt = stmt.where(self.model.status == status)

        stmt = (
            stmt.order_by(self.model.created_at.desc())
            .offset(offset)
            .limit(limit)
        )

        res = await db.execute(stmt)
        return res.scalars().all()

    async def list_for_company(
        self,
        db: AsyncSession,
        *,
        company_id,
        status: CompanyInvitationStatusEnum | None,
        offset: int = 0,
        limit: int = 20,
    ) -> Sequence[CompanyInvitation]:
        stmt = (select(self.model)
            .options(selectinload(self.model.company))
            .where(
            self.model.company_id == company_id,
        ))
        if status is not None:
            stmt = stmt.where(self.model.status == status)

        stmt = (
            stmt.order_by(self.model.created_at.desc())
            .offset(offset)
            .limit(limit)
        )

        res = await db.execute(stmt)
        return res.scalars().all()
