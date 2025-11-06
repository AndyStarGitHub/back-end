from typing import Generic, TypeVar, Type
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


T = TypeVar("T")


class BaseRepository(Generic[T]):
    def __init__(self, model: Type[T]):
        self.model = model

    async def get(self, db: AsyncSession, id_: int) -> T | None:
        res = await db.execute(select(self.model).where(self.model.id == id_))
        return res.scalars().first()

    async def list(
            self,
            db: AsyncSession,
            offset: int = 0,
            limit: int = 50
    ) -> list[T]:
        res = await db.execute(select(self.model).offset(offset).limit(limit))
        return list(res.scalars().all())
