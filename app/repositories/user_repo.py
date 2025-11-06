from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self):
        super().__init__(User)

    async def get_by_email(self, db: AsyncSession, email: str) -> User | None:
        res = await db.execute(select(User).where(User.email == email))
        return res.scalars().first()

    async def get_by_id(self, db: AsyncSession, user_id: int) -> User | None:
        res = await db.execute(select(User).where(User.id == user_id))
        return res.scalars().first()

    async def create(
            self,
            db: AsyncSession,
            *,
            email: str,
            full_name: str | None,
            hashed_password: str
    ) -> User:
        user = User(
            email=email,
            full_name=full_name,
            hashed_password=hashed_password,
            is_active=True
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    async def patch_user(
            self,
            db: AsyncSession,
            user_id: int,
            *,
            full_name: str | None = None,
            is_active: bool | None = None
    ) -> User | None:
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(**{k: v for k, v in {"full_name": full_name, "is_active": is_active}.items() if v is not None})
            .returning(User)
        )
        res = await db.execute(stmt)
        row = res.fetchone()
        if not row:
            return None
        await db.commit()
        return row[0]

    async def delete_user(self, db: AsyncSession, user_id: int) -> bool:
        res = await db.execute(delete(User).where(User.id == user_id))
        await db.commit()
        return res.rowcount > 0

    async def list_users(
            self,
            db: AsyncSession,
            *,
            offset: int = 0,
            limit: int = 50
    ) -> tuple[int, list[User]]:
        total = (await db.execute(
            select(func.count()).select_from(User))
                 ).scalar_one()
        result = await db.execute(
            select(User).order_by(User.id).offset(offset).limit(limit)
        )
        items = list(result.scalars().all())
        return total, items


user_repo = UserRepository()
