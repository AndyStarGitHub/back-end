from __future__ import annotations
from uuid import uuid4
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.repositories.user_repo import user_repo
from app.core.errors import (
    InvalidCredentials,
    InactiveUser,
    AuthError,
    NotFound,
    TokenDecodeError
)
from app.core.security import verify_password
from app.models.user import User


JWT_SECRET = settings.security.JWT_SECRET
JWT_ALG = settings.security.JWT_ALG
JWT_ISS = settings.security.JWT_ISS
JWT_EXPIRES_MIN = settings.security.JWT_EXPIRES_MIN

JWT_REFRESH_SECRET = settings.security.JWT_REFRESH_SECRET
JWT_REFRESH_EXPIRES_MIN = settings.security.JWT_REFRESH_EXPIRES_MIN
JWT_REFRESH_ALG = JWT_ALG


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def login_with_password(self, *, email: str, password: str) -> dict:
        user: User | None = await user_repo.get_by_email(self.db, email)
        if not user or not verify_password(password, user.hashed_password):
            raise InvalidCredentials("Invalid credentials")

        if getattr(user, "is_active", True) is False:
            raise InactiveUser()

        if not verify_password(password, user.hashed_password):
            raise InvalidCredentials()

        logger.info("user = {}", user)
        tokens = issue_tokens_for_user(user)
        logger.info("login_with_password before return tokens = {}", tokens)
        return tokens

    async def refresh_access_token(self, refresh_token: str) -> dict:
        try:
            payload = jwt.decode(
                refresh_token,
                settings.security.JWT_REFRESH_SECRET,
                algorithms=[settings.security.JWT_REFRESH_ALG],
            )
        except jwt.InvalidTokenError:
            raise InvalidCredentials("Invalid credentials")

        if payload.get("type") != "refresh":
            raise InvalidCredentials("Invalid credentials")

        user_id = payload.get("sub")
        if not user_id:
            raise InvalidCredentials("Invalid credentials")

        user = await user_repo.get_by_id(self.db, int(user_id))
        if not user:
            raise InvalidCredentials("Invalid credentials")

        new_access = create_access_token(sub=str(user.id), email=user.email)

        return {
            "access_token": new_access,
            "token_type": "bearer",
        }


def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            settings.security.JWT_SECRET,
            algorithms=[settings.security.JWT_ALG],
        )
    except jwt.PyJWTError as e:
        raise TokenDecodeError(f"Invalid access token: {e}")

    if payload.get("type") != "access":
        raise TokenDecodeError("Not an access token")

    return payload


def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(
        token,
        settings.security.JWT_SECRET,
        algorithms=[settings.security.JWT_ALG],
        options={"require": ["exp", "iat", "sub"]},
    )


def issue_tokens_for_user(user: User) -> dict:
    sub = str(user.id)
    logger.info("user email = {}", user.email)
    access = create_access_token(sub=sub, email=user.email)
    logger.info("access = {}", access)
    refresh = create_refresh_token(sub=sub)
    logger.info("refresh = {}", refresh)
    return {
        "access_token": access,
        "refresh_token": refresh,
        "token_type": "bearer",
    }


def create_access_token(sub: str, email: str) -> str:
    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=settings.security.JWT_EXPIRES_MIN)

    payload = {
        "iss": "local",
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
        "sub": sub,
        "email": email,
        "type": "access",
        "jti": uuid4().hex,
    }

    token = jwt.encode(
        payload,
        settings.security.JWT_SECRET,
        algorithm=settings.security.JWT_ALG,
    )
    return token


def create_refresh_token(sub: str) -> str:
    now = datetime.now(timezone.utc)
    exp = now + timedelta(
        minutes=settings.security.JWT_REFRESH_EXPIRES_MIN
    )

    payload = {
        "iss": "local",
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
        "sub": sub,
        "type": "refresh",
    }

    token = jwt.encode(
        payload,
        settings.security.JWT_REFRESH_SECRET,
        algorithm=settings.security.JWT_REFRESH_ALG,
    )
    return token
