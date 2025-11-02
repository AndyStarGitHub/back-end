from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import exc as sa_exc
import logging

from app.db.database import get_session, get_db
from app.core.security import hash_password
from app.repositories.user_repo import list_users, get_by_email, create
from app.schemas.common import PaginatedResponse
from app.schemas.user import UserCreate, UserUpdate, UserOut
from app.repositories import user_repo


log = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "",
    response_model=PaginatedResponse[UserOut],
    summary="Отримати список користувачів з пагінацією",
)
async def get_users(
    db: AsyncSession = Depends(get_db),
    limit: int = Query(
        10,
        ge=1,
        le=100,
        description="Скільки записів повернути"
    ),
    offset: int = Query(
        0,
        ge=0,
        description="Зсув від початку вибірки"
    ),
    search: Optional[str] = Query(
        None,
        description="Опційний пошук по email/full_name"
    ),
):
    total, items = await list_users(
        db,
        limit=limit,
        offset=offset,
        search=search
    )
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": items,
    }


@router.get("/{user_id}", response_model=UserOut)
async def get_user(
        user_id: int,
        db: AsyncSession = Depends(get_session)
):
    us = await user_repo.get_by_id(db, user_id)
    if not us:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    return UserOut.model_validate(us.__dict__)


@router.post(
    "",
    response_model=UserOut,
    status_code=201
)
async def create_user(
        payload: UserCreate,
        db: AsyncSession = Depends(get_session)
):
    if await get_by_email(db, payload.email):
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    user_obj = await create(db, payload)
    return UserOut.model_validate(user_obj)


@router.patch("/{user_id}", response_model=UserOut)
async def update_user(
        user_id: int,
        payload: UserUpdate,
        db: AsyncSession = Depends(get_session)
):
    hashed = hash_password(payload.password) if payload.password else None
    try:
        us = await user_repo.patch_user(
            db, user_id,
            full_name=payload.full_name,
            is_active=payload.is_active,
            hashed_password=hashed
        )
        if not us:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )
        log.info("User updated id=%s", user_id)
        return UserOut.model_validate(us.__dict__)
    except sa_exc.SQLAlchemyError as e:
        log.exception(
            "Failed to update user id=%s: %s",
            user_id, e
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to update user"
        )


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_user(
        user_id: int,
        db: AsyncSession = Depends(get_session)
):
    try:
        ok = await user_repo.delete_user(db, user_id)
        if not ok:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )
        log.info("User deleted id=%s", user_id)
        return None
    except sa_exc.SQLAlchemyError as exc:
        log.exception(
            "Failed to delete user id=%s: %s",
            user_id,
            exc
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to delete user"
        )
