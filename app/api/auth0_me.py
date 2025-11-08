from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import Principal, get_current_principal, get_current_identity, get_current_user_email
from app.db.database import get_db
from app.dependencies import get_current_user_auth0
from app.schemas.user import UserOut  # твій UserOut

router = APIRouter()

@router.get("/me")
async def auth0_me(
    payload = Depends(get_current_identity),
    email: str = Depends(get_current_user_email),
):
    # Повернемо базову інфу, щоб показати що все працює
    sub = payload.get("sub")
    iss = payload.get("iss")
    aud = payload.get("aud")
    return {
        "ok": True,
        "email": email,
        "sub": sub,
        "iss": iss,
        "aud": aud,
    }
