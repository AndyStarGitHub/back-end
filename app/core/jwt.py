from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
import jwt

from app.core.config import settings

JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-me")
JWT_ALG = os.getenv("JWT_ALG", "HS256")
JWT_ISS = os.getenv("JWT_ISS", "local")
JWT_EXPIRES_MIN = int(os.getenv("JWT_EXPIRES_MIN", "60"))

JWT_REFRESH_SECRET = getattr(settings, "JWT_REFRESH_SECRET", None) or JWT_SECRET
JWT_REFRESH_EXPIRES_DAYS = getattr(settings, "JWT_REFRESH_EXPIRES_DAYS", 7)
JWT_REFRESH_ALG = JWT_ALG



def create_access_token(*, sub: str, email: str, extra: dict | None = None) -> str:
    now = datetime.now(timezone.utc)
    payload: dict = {
        "iss": "local",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=JWT_EXPIRES_MIN)).timestamp()),
        "sub": sub,
        "email": email,
        "type": "access",
    }
    if extra:
        payload.update(extra)
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)
    return token



class TokenDecodeError(Exception):
    pass


def decode_local_token(token: str) -> dict:
    try:
        data = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALG],
            options={"require": ["iss", "sub", "exp"]},
            issuer=JWT_ISS,
        )
        return data
    except jwt.PyJWTError as e:
        raise TokenDecodeError(str(e))


def create_refresh_token(*, sub: str) -> str:
    now = datetime.now(timezone.utc)
    payload: dict = {
        "iss": "local",
        "iat": int(now.timestamp()),
        "exp": int(
            (now + timedelta(days=JWT_REFRESH_EXPIRES_DAYS)).timestamp()
        ),
        "sub": sub,
        "type": "refresh",
    }
    token = jwt.encode(payload, JWT_REFRESH_SECRET, algorithm=JWT_REFRESH_ALG)
    return token


def decode_refresh_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            JWT_REFRESH_SECRET,
            algorithms=[JWT_REFRESH_ALG],
            options={"require": ["exp", "sub"]},
        )
    except jwt.PyJWTError as e:
        raise TokenDecodeError(str(e))

    if payload.get("type") != "refresh":
        # Не дамо використати access або будь-що інше як refresh
        raise TokenDecodeError("Not a refresh token")

    return payload

