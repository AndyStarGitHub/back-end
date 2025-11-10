from __future__ import annotations

from typing import TypeVar, Generic, Type, Tuple, Optional, Any
from sqlalchemy import select, update, delete, func, desc
from sqlalchemy.ext.asyncio import AsyncSession


T = TypeVar("T")


class BaseRepository(Generic[T]):

    def __init__(self, model: Type[T]):
        self.model: Type[T] = model

    async def get_by_id(self, db: AsyncSession, obj_id: int) -> T | None:
        res = await db.execute(
            select(self.model).where(self.model.id == obj_id)
        )
        return res.scalars().first()

    async def create_one(self, db: AsyncSession, **values) -> T:
        obj = self.model(**values)
        db.add(obj)
        await db.commit()
        await db.refresh(obj)
        return obj

    async def update_one(
            self,
            db: AsyncSession,
            obj_id: int,
            **values
    ) -> T | None:

        values = {k: v for k, v in values.items() if v is not None}
        if not values:
            return await self.get_by_id(db, obj_id)

        stmt = (
            update(self.model)
            .where(self.model.id == obj_id)
            .values(**values)
            .returning(self.model)
        )
        res = await db.execute(stmt)
        row = res.fetchone()
        if not row:
            return None
        await db.commit()
        return row[0]

    async def delete_one(self, db: AsyncSession, obj_id: int) -> bool:
        res = await db.execute(
            delete(self.model).where(self.model.id == obj_id)
        )
        await db.commit()
        return res.rowcount > 0

    async def get_all_paginated(
        self,
        db: AsyncSession,
        *,
        offset: int = 0,
        limit: int = 50,
        order_by: Optional[Any] = None,
        descending: bool = True,
    ) -> Tuple[int, list[T]]:
        total = (
            await db.execute(select(func.count()).select_from(self.model))
        ).scalar_one()

        ob = order_by or getattr(self.model, "created_at", self.model.id)
        if descending:
            ob = desc(ob)

        result = await db.execute(
            select(self.model)
            .order_by(ob)
            .offset(offset)
            .limit(limit)
        )
        items = list(result.scalars().all())
        return total, items

    async def get_one_by(self, db: AsyncSession, **filters) -> Optional[T]:
        res = await db.execute(select(self.model).filter_by(**filters))
        return res.scalars().first()
