from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFound, Conflict
from app.core.security import hash_password
from app.repositories.user_repo import user_repo
from app.schemas.user import UserCreate, UserUpdate
from app.models.user import User


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_user(self, payload: UserCreate) -> User:
        existing = await user_repo.get_by_email(self.db, payload.email)
        if existing:
            raise Conflict("User with this email already exists")

        user = await user_repo.create_one(
            self.db,
            email=payload.email,
            full_name=payload.full_name,
            hashed_password=hash_password(payload.password),
            is_active=True,
        )
        return user

    async def get_user(self, user_id: int) -> User:
        user = await user_repo.get_by_id(self.db, user_id)
        if not user:
            raise NotFound("User not found")
        return user

    async def list_users(self, *, limit: int = 10, offset: int = 0):
        from app.models.user import User
        return await user_repo.get_all_paginated(
            self.db,
            offset=offset,
            limit=limit,
            order_by=User.created_at,
            descending=True,
        )

    async def update_user(self, user_id: int, payload: UserUpdate) -> User:
        updates = payload.model_dump(exclude_unset=True, exclude_none=True)

        updates.pop("password", None)
        updates.pop("hashed_password", None)

        user = await user_repo.update_one(self.db, user_id, **updates)
        if not user:
            raise NotFound("User not found")
        return user

    async def delete_user(self, user_id: int) -> bool:
        return await user_repo.delete_one(self.db, user_id)
