from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.company import Company
from app.repositories.base import BaseRepository


class CompanyRepository(BaseRepository[Company]):
    def __init__(self) -> None:
        super().__init__(Company)

    async def get_all(
        self,
        db: AsyncSession,
    ) -> list[Company]:

        res = await db.execute(select(Company))
        return list(res.scalars().all())

    async def get_public_paginated(
        self,
        db: AsyncSession,
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[int, list[Company]]:
        total_result = await db.execute(
            select(func.count()).select_from(Company).where(
                Company.visibility == "public",
            )
        )
        total = total_result.scalar_one()

        result = await db.execute(
            select(Company)
            .where(Company.visibility == "public")
            .offset(offset)
            .limit(limit)
        )
        items = list(result.scalars().all())
        return total, items

    async def get_by_owner_paginated(
        self,
        db: AsyncSession,
        owner_id: int,
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[int, list[Company]]:
        total_result = await db.execute(
            select(func.count()).select_from(Company).where(
                Company.owner_id == owner_id,
            )
        )
        total = total_result.scalar_one()

        result = await db.execute(
            select(Company)
            .where(Company.owner_id == owner_id)
            .offset(offset)
            .limit(limit)
        )
        items = list(result.scalars().all())
        return total, items
