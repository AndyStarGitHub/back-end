from loguru import logger
import datetime as dt
from typing import Optional, Any

import jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.core.jwt import create_access_token, create_refresh_token
from app.models.user import User



pwd_context = CryptContext(
    schemes=["bcrypt_sha256", "bcrypt"],
    deprecated="auto",
    bcrypt__truncate_error=False,
)


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    ok, new_hash = pwd_context.verify_and_update(plain, hashed)
    return ok


# def create_access_token(
#         *,
#         sub: str,
#         email: str,
#         extra: Optional[dict[str, Any]] = None,
# ) -> str:
#     now = dt.datetime.utcnow()
#     exp = now + dt.timedelta(minutes=settings.security.JWT_EXPIRES_MIN)
#
#     payload: dict[str, Any] = {
#         "sub": sub,
#         "email": email,  # <-- тепер email завжди є в токені
#         "iat": int(now.timestamp()),
#         "exp": int(exp.timestamp()),
#         "type": "access",  # корисно мати тип токена
#     }
#
#     if extra:
#         payload.update(extra)
#
#     token = jwt.encode(
#         payload,
#         settings.security.JWT_SECRET,
#         algorithm=settings.security.JWT_ALG,
#     )
#     return token



def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(
        token,
        settings.security.JWT_SECRET,
        algorithms=[settings.security.JWT_ALG],
        options={"require": ["exp", "iat", "sub"]},
    )


def issue_tokens_for_user(user: User) -> dict:
    """
    Повертає дикт з access + refresh токенами для користувача.
    """
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

