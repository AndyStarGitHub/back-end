from typing import Dict, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth0 import verify_auth0_token, extract_email
from app.core.errors import NotAuthenticated, TokenInvalid, NotFound
from app.core.security import decode_token
from app.db.database import get_db
from app.dependencies import bearer
from app.models import User
from app.repositories.user_repo import user_repo
from app.core.jwt import decode_local_token, TokenDecodeError
from app.services.auth_service import AuthService


bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user_local(
    creds: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
):
    if not creds or not creds.scheme.lower() == "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    token = creds.credentials

    try:
        payload = decode_local_token(token)
    except TokenDecodeError:
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

    user = await user_repo.get_by_id(db, int(user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    if getattr(user, "is_active", True) is False:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is inactive"
        )

    return user




async def get_current_identity(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
):
    if creds is None or creds.scheme.lower() != "bearer":
        raise NotAuthenticated("Missing bearer token")
    token = creds.credentials
    try:
        payload = decode_token(token)
    except Exception:
        raise TokenInvalid("Invalid token")
    return payload


class Principal(BaseModel):
    sub: str
    email: str | None = None
    scope: str | None = None
    raw: dict


async def get_current_user_auth0(
    creds: HTTPAuthorizationCredentials = Depends(bearer),
    db: AsyncSession = Depends(get_db),
):
    if not creds or creds.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    payload = verify_auth0_token(creds.credentials)
    email = extract_email(payload)

    user = await user_repo.get_by_email(db, email)
    if not user:
        user = await user_repo.create_from_auth0(db, email=email)

    return user


async def get_current_principal(
    creds: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> Principal:
    if not creds or creds.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token"
        )

    try:
        payload = verify_auth0_token(creds.credentials)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

    return Principal(
        sub=payload.get("sub"),
        email=extract_email(payload),
        scope=payload.get("scope"),
        raw=payload,
    )


async def require_auth(
        _: Principal = Depends(get_current_principal)
) -> None:
    return None


async def get_current_user_email(
    payload: Dict[str, Any] = Depends(get_current_identity),
) -> str:
    email = extract_email(payload)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email claim not found"
        )
    return email

async def optional_current_user_dep(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """
    Повертає User або None. Ніколи не підіймає 401.
    Використовується там, де логіка дозволяє анонімний доступ, але сервісу зручно знати користувача, якщо він є.
    """
    try:
        # якщо токена нема — просто None
        if creds is None or creds.scheme.lower() != "bearer":
            return None

        claims = verify_auth0_token(creds.credentials)
        email = extract_email(claims)
        if not email:
            return None

        user = await user_repo.get_by_email(db, email)
        return user
    except Exception:
        # будь-які проблеми з токеном — мовчки повертаємо None (бо опційно)
        return None


def auth_service_dep(db: AsyncSession = Depends(get_db)) -> AuthService:
    return AuthService(db=db)


async def get_current_user(
    identity: dict = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
):
    user_id = identity.get("sub")
    if not user_id:
        raise TokenInvalid("Invalid token payload")
    user = await user_repo.get_by_id(db, int(user_id))
    if not user:
        raise NotFound("User not found")
    return user