from __future__ import annotations

from typing import Sequence, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company_join_request import CompanyJoinRequest
from app.repositories.base import BaseRepository


class CompanyJoinRequestRepository(BaseRepository[CompanyJoinRequest]):
    def __init__(self) -> None:
        super().__init__(CompanyJoinRequest)

    async def list_for_user(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        status: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> Sequence[CompanyJoinRequest]:
        stmt = select(CompanyJoinRequest).where(
            CompanyJoinRequest.user_id == user_id,
        )

        if status is not None:
            stmt = stmt.where(CompanyJoinRequest.status == status)

        stmt = (
            stmt.order_by(CompanyJoinRequest.created_at.desc())
            .offset(offset)
            .limit(limit)
        )

        res = await db.execute(stmt)
        return res.scalars().all()

    async def list_for_company(
        self,
        db: AsyncSession,
        *,
        company_id: Any,
        status: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> Sequence[CompanyJoinRequest]:
        stmt = select(CompanyJoinRequest).where(
            CompanyJoinRequest.company_id == company_id,
        )

        if status is not None:
            stmt = stmt.where(CompanyJoinRequest.status == status)

        stmt = (
            stmt.order_by(CompanyJoinRequest.created_at.desc())
            .offset(offset)
            .limit(limit)
        )

        res = await db.execute(stmt)
        return res.scalars().all()
