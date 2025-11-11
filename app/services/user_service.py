from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFound, Conflict, Forbidden, BadRequest
from app.core.security import hash_password
from app.repositories.user_repo import user_repo
from app.schemas.user import UserCreate, UserUpdate
from app.models.user import User


class UserService:
    # def __init__(self, db: AsyncSession):
    #     self.db = db


    def __init__(self, db: AsyncSession, current_user: User | None = None):
        self.db = db
        self.current_user = current_user


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

    def _ensure_self(self, target_user_id: int):
        if not self.current_user or self.current_user.id != target_user_id:
            # 403 за логікою задачі “можна тільки над собою”
            raise Forbidden("You can only modify your own profile")

    async def self_update_profile(self, user_id: int, full_name: str | None) -> User:
        self._ensure_self(user_id)

        # жодних змін email — він навіть не приходить у схемі
        updates = {}
        if full_name is not None:
            updates["full_name"] = full_name

        if not updates:
            # нічого не змінюємо
            user = await user_repo.get_by_id(self.db, user_id)
            if not user:
                raise NotFound("User not found")
            return user

        updated = await user_repo.update_one(self.db, user_id, updates)
        if not updated:
            raise NotFound("User not found")
        return updated

    async def self_change_password(self, user_id: int, new_password: str) -> User:
        self._ensure_self(user_id)

        if len(new_password) < 6:
            raise BadRequest("Password too short")

        updated = await user_repo.update_one(
            self.db, user_id, {"hashed_password": hash_password(new_password)}
        )
        if not updated:
            raise NotFound("User not found")
        return updated

    async def self_delete(self, user_id: int) -> bool:
        self._ensure_self(user_id)
        return await user_repo.delete_one(self.db, user_id)
