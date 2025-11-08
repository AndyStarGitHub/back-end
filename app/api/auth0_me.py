from fastapi import APIRouter, Depends

from app.core.deps import (
    get_current_identity,
    get_current_user_email
)


router = APIRouter()


@router.get("/me")
async def auth0_me(
    payload = Depends(get_current_identity),
    email: str = Depends(get_current_user_email),
):
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
