from typing import Optional, Dict, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth0 import verify_auth0_token
from app.core.config import settings
from app.db.database import get_db
from app.repositories.user_repo import get_by_id  # або get_by_email — див. нижче
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
    creds: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> Dict[str, Any]:
    if not creds or creds.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")

    token = creds.credentials

    # 1) Локальний JWT
    payload = decode_token(token)
    if payload:
        # очікуємо, що у локальному токені є 'sub' або 'email'
        user_email = payload.get("email") or payload.get("sub")
        if not user_email:
            raise HTTPException(status_code=401, detail="Local token missing email/sub")
        return {"source": "local", "email": user_email, "payload": payload}

    # 2) Auth0
    try:
        payload = verify_auth0_token(token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

    user_email = payload.get(settings.auth0.EMAIL_CLAIM)
    if not user_email:
        raise HTTPException(status_code=401, detail="Auth0 token missing email claim")

    return {"source": "auth0", "email": user_email, "payload": payload}
