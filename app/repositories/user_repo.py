from typing import Optional, Sequence

from pydantic import EmailStr
from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.user import User
from app.schemas.user import UserCreate


async def get_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
    res = await db.execute(select(User).where(User.id == user_id))
    return res.scalar_one_or_none()


async def get_by_email(
        db: AsyncSession,
        email: EmailStr
) -> Optional[User]:
    res = await db.execute(select(User).where(User.email == email))
    return res.scalar_one_or_none()


async def list_users(
    db: AsyncSession,
    limit: int,
    offset: int,
    search: Optional[str] = None,
) -> tuple[int, Sequence[User]]:

    stmt = select(User)
    count_stmt = select(func.count()).select_from(User)

    if search:
        like = f"%{search}%"
        stmt = stmt.where((User.email.ilike(like)) | (User.full_name.ilike(like)))
        count_stmt = count_stmt.where((User.email.ilike(like)) | (User.full_name.ilike(like)))

    stmt = stmt.order_by(User.created_at.desc()).offset(offset).limit(limit)

    total = (await db.execute(count_stmt)).scalar_one()
    items = (await db.execute(stmt)).scalars().all()

    return total, items


async def create(db: AsyncSession, payload: UserCreate) -> User:
    user = User(
        email=payload.email,
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def create_from_auth0(db: AsyncSession, email: str) -> User:
    user = User(
        email=email,
        full_name="",
        hashed_password="",
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def patch_user(
        db: AsyncSession,
        user_id: int,
        *,
        full_name: str | None,
        is_active: bool | None,
        hashed_password: str | None
) -> Optional[User]:
    values = {}
    if full_name is not None: values["full_name"] = full_name
    if is_active is not None: values["is_active"] = is_active
    if hashed_password is not None: values["hashed_password"] = hashed_password
    if not values:
        return await get_by_id(db, user_id)
    await db.execute(update(User).where(User.id == user_id).values(**values))
    await db.commit()
    return await get_by_id(db, user_id)


async def delete_user(db: AsyncSession, user_id: int) -> bool:
    res = await db.execute(delete(User).where(User.id == user_id))
    await db.commit()
    return (res.rowcount or 0) > 0


async def create_from_email(db: AsyncSession, email: str) -> User:
    user = User(email=email, hashed_password="")
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
