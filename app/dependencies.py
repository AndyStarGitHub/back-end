# app/dependencies/auth0.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth0 import verify_auth0_token
from app.core.config import settings
from app.db.database import get_db
from app.repositories.user_repo import get_by_email, create_from_email

bearer = HTTPBearer(auto_error=False)

async def get_current_user_auth0(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: AsyncSession = Depends(get_db),
):
    if creds is None or not creds.scheme.lower() == "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")

    token = creds.credentials
    try:
        claims = await verify_auth0_token(token)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token: {e}")

    # спробувати дістати email з неймспейс-клейму, або "email"
    email_claim_name = getattr(settings, "AUTH0_EMAIL_CLAIM", None) or settings.auth0.EMAIL_CLAIM
    email = claims.get(email_claim_name) or claims.get("email")
    if not email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email claim not found in token")

    user = await get_by_email(db, email)
    if user is None:
        user = await create_from_email(db, email)  # простий створювач: email, is_active=True, created_at=...

    return user
