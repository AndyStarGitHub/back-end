from loguru import logger
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



bearer = HTTPBearer(auto_error=False)






async def get_current_identity(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
):
    logger.info("get_current_identity: raw creds = {}", creds)

    if creds is None or creds.scheme.lower() != "bearer":
        logger.warning("Missing or wrong scheme in Authorization header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token"
        )

    token = creds.credentials
    logger.info("get_current_identity: got token (first 20 chars) = {}", token[:20])

    try:
        claims = verify_auth0_token(token)
        logger.info("get_current_identity: decoded claims keys = {}", list(claims.keys()))
    except Exception as e:
        logger.exception("Token verification failed: {}", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

    return {
        "email": extract_email(claims),
        "source": "auth0",
        "payload": claims,
    }





# async def get_current_identity(
#     creds: HTTPAuthorizationCredentials | None = Depends(bearer),
# ):
#     logger.info("get_current_identity: raw creds = {}", creds)
#     if creds is None or creds.scheme.lower() != "bearer":
#         logger.warning("Missing or wrong scheme in Authorization header")
#         raise NotAuthenticated("Missing bearer token")
#     token = creds.credentials
#     logger.info("get_current_identity: got token (first 20 chars) = {}", token[:20])
#     try:
#         payload = decode_token(token)
#     except Exception:
#         raise TokenInvalid("Invalid token")
#     return payload


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


# async def get_current_principal(
#     creds: HTTPAuthorizationCredentials = Depends(bearer_scheme),
# ) -> Principal:
#     if not creds or creds.scheme.lower() != "bearer":
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Missing bearer token"
#         )
#
#     try:
#         payload = verify_auth0_token(creds.credentials)
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Invalid token"
#         )
#
#     return Principal(
#         sub=payload.get("sub"),
#         email=extract_email(payload),
#         scope=payload.get("scope"),
#         raw=payload,
#     )


# async def require_auth(
#         _: Principal = Depends(get_current_principal)
# ) -> None:
#     return None


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


async def get_current_user_auth0(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: AsyncSession = Depends(get_db),
):
    if creds is None or creds.scheme.lower() != "bearer":
        logger.info("No credentials provided")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")

    logger.info("Auth header scheme=%s", getattr(creds, "scheme", None))

    token = creds.credentials
    logger.info("Got bearer token with length=%s", len(token) if token else 0)

    try:
        claims = verify_auth0_token(token)
        logger.info("verify_auth0_token OK: sub=%s aud=%s iss=%s",
                 claims.get("sub"), claims.get("aud"), claims.get("iss"))
        return {
            "source": "auth0",
            "email": extract_email(claims),
            "payload": claims,
        }
    except Exception as e:
        # важливо: зловили і залогували ПЕРЕД тим як віддати 401
        logger.exception("verify_auth0_token FAILED: %s", e)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


    payload = verify_auth0_token(creds.credentials)
    email = extract_email(payload)
    if not email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email claim not found")

    user = await user_repo.get_by_email(db, email)
    if not user:
        # автостворення лайт-юзера
        user = await user_repo.create(
            db,
            email=email,
            full_name=None,
            hashed_password="",
        )
    return user
