from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.database import get_db
from app.schemas.auth import LoginInput, TokenOut
from app.repositories.user_repo import get_by_email
from app.core.security import verify_password
from app.core.jwt import create_access_token
from app.schemas.user import UserOut

router = APIRouter()

@router.post("/login", response_model=TokenOut, summary="Login with email & password")
async def login(payload: LoginInput, db: AsyncSession = Depends(get_db)):
    user = await get_by_email(db, payload.email)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if getattr(user, "is_active", True) is False:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is inactive")

    token = create_access_token(sub=str(user.id), email=user.email)
    return TokenOut(access_token=token)


@router.get("/me", response_model=UserOut, summary="Current user profile (by token)")
async def read_me(current_user = Depends(get_current_user)):
    return current_user
