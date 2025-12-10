from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status
)
from loguru import logger
from sqlalchemy import exc as sa_exc

from starlette.responses import Response

from app.core.deps import get_current_user
from app.core.errors import Forbidden, NotFound
from app.models import User
from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserOut,
    UsersListResponse,
    UserDetailResponse, UserPasswordChange
)

from app.services.deps import get_user_service, user_service_dep
from app.services.user_service import UserService


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
        logger.exception("Failed to list users: {}", exc)
        raise HTTPException(status_code=500, detail="Failed to list users")


@router.get("/me", response_model=UserDetailResponse)
async def read_current_user(
    current_user: User = Depends(get_current_user),
) -> User:
    return current_user


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
        logger.exception("Failed to fetch user id=: {}}", (user_id, exc))
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
        logger.exception("Failed to create user: {}", exc)
        raise HTTPException(status_code=500, detail="Failed to create user")


@router.patch("/me", response_model=UserOut)
async def update_own_profile(
    payload: UserUpdate,
    svc: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_user),
):
    try:
        user = await svc.update_user(current_user.id, payload)
        return UserOut.model_validate(user)
    except sa_exc.SQLAlchemyError as exc:
        logger.exception(
            "Failed to update own profile for user id=: {}",
            (current_user.id, exc),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user",
        )


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_own_profile(
    svc: UserService = Depends(user_service_dep),
    current_user: User = Depends(get_current_user),
):
    await svc.delete_user(user_id=current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/me/password", status_code=status.HTTP_204_NO_CONTENT)
async def change_own_password(
    payload: UserPasswordChange,
    svc: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_user),
):
    try:
        await svc.change_password(
            current_user=current_user,
            old_password=payload.old_password,
            new_password=payload.new_password,
        )
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    except Forbidden as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        )
    except NotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    except sa_exc.SQLAlchemyError as exc:
        logger.exception(
            "Failed to change password for user id=: {}",
            (current_user.id, exc),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password",
        )
