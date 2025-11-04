import datetime as dt
from typing import Optional, Any

import jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(
    schemes=["bcrypt_sha256", "bcrypt"],   # нові паролі йдуть в bcrypt_sha256, старі bcrypt ще читаємо
    deprecated="auto",
    bcrypt__truncate_error=False,          # НЕ падати на >72 байти для legacy bcrypt
)


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)

def verify_password(plain: str, hashed: str) -> bool:
    # verify_and_update: якщо хеш застарілий (bcrypt), поверне new_hash для перевидачі
    ok, new_hash = pwd_context.verify_and_update(plain, hashed)
    # Поверни булеве — оновлення (rehash) зробимо на рівні роутера, якщо потрібно
    return ok


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
