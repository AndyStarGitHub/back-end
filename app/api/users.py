from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import exc as sa_exc
import logging

from app.core.errors import NotFound, Conflict
from app.db.database import get_db

from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserOut,
    UsersListResponse,
    UserDetailResponse
)
from app.repositories import user_repo
from app.services import user_service

log = logging.getLogger(__name__)
router = APIRouter()


@router.get("", response_model=UsersListResponse)
async def list_users(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    total, items = await user_service.list_users(
        db,
        limit=limit,
        offset=offset
    )
    return UsersListResponse(
        total=total,
        limit=limit,
        offset=offset,
        items=[UserOut.model_validate(u.__dict__) for u in items],
    )


@router.get("/{user_id}", response_model=UserDetailResponse)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    try:
        user = await user_service.get_user(db, user_id)
        return UserDetailResponse.model_validate(user.__dict__)
    except NotFound as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("", response_model=UserDetailResponse, status_code=201)
async def create_user(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    try:
        user = await user_service.create_user(db, payload)
        return UserDetailResponse.model_validate(user.__dict__)
    except Conflict as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.patch("/{user_id}", response_model=UserOut)
async def update_user(
    user_id: int,
    payload: UserUpdate,
    db: AsyncSession = Depends(get_db),
):
    try:
        user = await user_service.update_user(db, user_id, payload)
        return UserOut.model_validate(user.__dict__)
    except NotFound as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_user(
        user_id: int,
        db: AsyncSession = Depends(get_db)
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
