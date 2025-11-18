from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFound, Conflict, Forbidden
from app.core.security import hash_password, verify_password
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
        data = payload.model_dump(exclude_unset=True, exclude_none=True)

        if "email" in data:
            raise Conflict("Email cannot be changed")

        password = data.pop("password", None)

        updates: dict = {}

        if "full_name" in data:
            updates["full_name"] = data["full_name"]

        if not updates:
            user = await user_repo.get_by_id(self.db, user_id)
            if not user:
                raise NotFound("User not found")
            return user

        user = await user_repo.update_one(self.db, user_id, **updates)
        if not user:
            raise NotFound("User not found")
        return user

    async def change_password(
            self,
            current_user: User,
            user_id: int,
            old_password: str,
            new_password: str,
    ) -> User:

        if current_user.id != user_id:
            raise Forbidden("You can only change your own password")

        user = await user_repo.get_by_id(self.db, user_id)
        if not user:
            raise NotFound("User not found")

        if not verify_password(old_password, user.hashed_password):
            raise Forbidden("Old password is incorrect")

        new_hashed = hash_password(new_password)

        user = await user_repo.update_one(
            self.db,
            user_id,
            hashed_password=new_hashed,
        )
        if not user:
            raise NotFound("User not found")

        return user

    async def delete_user(self, user_id: int) -> bool:
        return await user_repo.delete_one(self.db, user_id)

    async def self_delete(self, user_id: int) -> bool:
        return await user_repo.delete_one(self.db, user_id)
