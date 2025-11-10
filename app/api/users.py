from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status
)
from sqlalchemy import exc as sa_exc
import logging

from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserOut,
    UsersListResponse,
    UserDetailResponse
)

from app.services.deps import get_user_service
from app.services.user_service import UserService


log = logging.getLogger(__name__)
router = APIRouter()


@router.get("", response_model=UsersListResponse)
async def list_users(
    offset: int = 0,
    limit: int = 50,
    svc: UserService = Depends(get_user_service),
):
    try:
        total, items = await svc.list_users(offset=offset, limit=limit)
        return UsersListResponse(total=total, items=items)
    except sa_exc.SQLAlchemyError as exc:
        log.exception("Failed to list users: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to list users")


@router.get("/{user_id}", response_model=UserDetailResponse)
async def get_user_by_id(
    user_id: int,
    svc: UserService = Depends(get_user_service),
):
    try:
        user = await svc.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return UserDetailResponse.model_validate(user)
    except sa_exc.SQLAlchemyError as exc:
        log.exception("Failed to fetch user id=%s: %s", user_id, exc)
        raise HTTPException(status_code=500, detail="Failed to fetch user")


@router.post(
    "",
    response_model=UserDetailResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_user(
    payload: UserCreate,
    svc: UserService = Depends(get_user_service),
):
    try:
        user = await svc.create_user(payload)
        return UserDetailResponse.model_validate(user)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except sa_exc.SQLAlchemyError as exc:
        log.exception("Failed to create user: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to create user")


@router.patch("/{user_id}", response_model=UserOut)
async def update_user(
    user_id: int,
    payload: UserUpdate,
    svc: UserService = Depends(get_user_service),
):
    try:
        user = await svc.update_user(user_id, payload)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return UserOut.model_validate(user)
    except sa_exc.SQLAlchemyError as exc:
        log.exception("Failed to update user id=%s: %s", user_id, exc)
        raise HTTPException(status_code=500, detail="Failed to update user")


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    svc: UserService = Depends(get_user_service)
):
    try:
        ok = await svc.delete_user(user_id)
        if not ok:
            raise HTTPException(status_code=404, detail="User not found")
        log.info("User deleted id=%s", user_id)
        return
    except sa_exc.SQLAlchemyError as exc:
        log.exception("Failed to delete user id=%s: %s", user_id, exc)
        raise HTTPException(status_code=500, detail="Failed to delete user")
