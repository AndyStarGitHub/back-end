from typing import Optional, Dict, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth0 import verify_auth0_token, extract_email
from app.core.config import settings
from app.db.database import get_db
from app.repositories.user_repo import get_by_id
from app.core.jwt import decode_local_token, TokenDecodeError
from app.core.security import decode_token


bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
):
    if not creds or not creds.scheme.lower() == "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    token = creds.credentials
    # тут у майбутньому додамо гілку для Auth0; зараз — тільки локальний JWT
    try:
        payload = decode_local_token(token)
    except TokenDecodeError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    # Ми клали sub = user.id
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    user = await get_by_id(db, int(user_id))
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    if getattr(user, "is_active", True) is False:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is inactive")

    return user


async def get_current_identity(
    creds: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> Dict[str, Any]:
    if creds.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid auth scheme")
    payload = verify_auth0_token(creds.credentials)  # кидає 401 якщо невалідний
    return payload


class Principal(BaseModel):
    sub: str
    email: str | None = None
    scope: str | None = None
    raw: dict

async def get_current_principal(
    creds: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> Principal:
    if not creds or creds.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")

    try:
        payload = verify_auth0_token(creds.credentials)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    return Principal(
        sub=payload.get("sub"),
        email=extract_email(payload),
        scope=payload.get("scope"),
        raw=payload,
    )


# Якщо треба: “просто перевірити, що токен валідний”
async def require_auth(_: Principal = Depends(get_current_principal)) -> None:
    return None


async def get_current_user_email(
    payload: Dict[str, Any] = Depends(get_current_identity),
) -> str:
    email = extract_email(payload)
    if not email:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Email claim not found")
    return email
