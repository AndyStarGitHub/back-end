from typing import Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFound, Conflict
from app.core.security import hash_password
from app.repositories import user_repo
from app.schemas.user import UserCreate, UserUpdate
from app.models.user import User


async def create_user(db: AsyncSession, payload: UserCreate) -> User:
    existing = await user_repo.get_by_email(db, payload.email)
    if existing:
        raise Conflict("User with this email already exists")

    user = await user_repo.create(
        db,
        email=payload.email,
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
    )
    return user


async def get_user(db: AsyncSession, user_id: int) -> User:
    user = await user_repo.get_by_id(db, user_id)
    if not user:
        raise NotFound("User not found")
    return user


async def list_users(
    db: AsyncSession, *, limit: int = 10, offset: int = 0
) -> Tuple[int, list[User]]:
    total, items = await user_repo.list_users(db, limit=limit, offset=offset)
    return total, items


async def update_user(
        db: AsyncSession,
        user_id: int,
        payload: UserUpdate
) -> User:

    updates = payload.model_dump(exclude_unset=True, exclude_none=True)

    updates.pop("password", None)
    updates.pop("hashed_password", None)

    user = await user_repo.patch_user(
        db,
        user_id,
        full_name=updates.get("full_name"),
        is_active=updates.get("is_active"),
    )
    if not user:
        raise NotFound("User not found")

    return user
