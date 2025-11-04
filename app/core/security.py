import datetime as dt
from typing import Optional, Any

import jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(sub: str, extra: Optional[dict[str, Any]] = None) -> str:
    """
    sub — ідентифікатор користувача (наприклад email або user_id).
    """
    now = dt.datetime.utcnow()
    exp = now + dt.timedelta(minutes=settings.security.JWT_EXPIRES_MIN)
    payload = {
        "sub": sub,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
    }
    if extra:
        payload.update(extra)

    token = jwt.encode(payload, settings.security.JWT_SECRET, algorithm=settings.security.JWT_ALG)
    return token


def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(
        token,
        settings.security.JWT_SECRET,
        algorithms=[settings.security.JWT_ALG],
        options={"require": ["exp", "iat", "sub"]},
    )
