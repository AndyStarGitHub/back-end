import jwt
from loguru import logger
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.repositories import user_repo
from app.repositories.user_repo import user_repo
from app.schemas.auth import TokenResponse, LoginRequest
from app.schemas.user import UserOut
from app.services.auth_service import (
    AuthService,
    decode_token,
    create_access_token
)

router = APIRouter()


def auth_service_dep(db: AsyncSession = Depends(get_db)) -> AuthService:
    return AuthService(db=db)


class SignInPayload(BaseModel):
    email: EmailStr
    password: str


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK
)
async def login(
        payload: LoginRequest,
        svc: AuthService = Depends(auth_service_dep)
):
    logger.info("Logit started:", payload.email)
    return await svc.login_with_password(
        email=payload.email,
        password=payload.password
    )


async def _current_user(request: Request, db: AsyncSession) -> User:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Bearer token"
        )

    token = auth.removeprefix("Bearer ").strip()
    try:
        payload = decode_token(token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )

    us = await user_repo.get_by_id(db, int(user_id))
    if not us:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    return us


@router.get("/me", response_model=UserOut)
async def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/auth/debug-headers")
async def debug_headers(req: Request):
    from loguru import logger
    auth = req.headers.get("authorization")
    logger.info("DEBUG /auth/debug-headers, Authorization = {}", auth)
    return {"authorization": auth}


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/refresh")
async def refresh_token_endpoint(
    body: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        payload = jwt.decode(
            body.refresh_token,
            settings.security.JWT_REFRESH_SECRET,
            algorithms=[settings.security.JWT_REFRESH_ALG],
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    user = await user_repo.get_by_id(db, int(user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    new_access = create_access_token(sub=str(user.id), email=user.email)

    return {
        "access_token": new_access,
        "token_type": "bearer",
    }
