from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
import jwt

JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-me")
JWT_ALG = os.getenv("JWT_ALG", "HS256")
JWT_ISS = os.getenv("JWT_ISS", "local")
JWT_EXPIRES_MIN = int(os.getenv("JWT_EXPIRES_MIN", "60"))


def create_access_token(
        *, sub: str,
        email: str | None = None,
        extra: dict | None = None
) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "iss": JWT_ISS,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=JWT_EXPIRES_MIN)).timestamp()),
        "sub": sub,
    }
    if email:
        payload["email"] = email
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
