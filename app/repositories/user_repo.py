from __future__ import annotations

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self):
        super().__init__(User)

    async def get_by_email(self, db: AsyncSession, email: str) -> User | None:
        logger.info("Email injected: {}", email)
        res = await db.execute(select(User).where(User.email == email))
        logger.info("Res: {}", res)
        return res.scalars().first()

    async def create_from_email(self, db: AsyncSession, email: str) -> User:
        user = User(email=email, hashed_password="")
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user


user_repo = UserRepository()
