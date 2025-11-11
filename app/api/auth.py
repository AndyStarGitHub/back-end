from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_identity, auth_service_dep
from app.core.errors import InvalidCredentials, InactiveUser
from app.models.user import User
from app.repositories import user_repo
from app.core.security import decode_token
from app.repositories.user_repo import user_repo
from app.schemas.user import UserOut
from app.services.auth_service import AuthService

router = APIRouter()


router = APIRouter()

class SignInPayload(BaseModel):
    email: EmailStr
    password: str

@router.post("/login")
async def login(payload: SignInPayload, svc: AuthService = Depends(auth_service_dep)):
    try:
        result = await svc.login_with_password(email=payload.email, password=payload.password)
        # бажано серіалізувати user через схему
        return {
            "access_token": result["access_token"],
            "token_type": "bearer",
            "user": UserOut.model_validate(result["user"]),
        }
    except InvalidCredentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    except InactiveUser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is inactive"
        )



async def _current_user(request: Request, db: AsyncSession) -> User:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Bearer token"
        )

    token = auth.removeprefix("Bearer ").strip()
    try:
        payload = decode_token(token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )

    u = await user_repo.get_by_id(db, int(user_id))
    if not u:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    return u


@router.get("/me")
async def me(identity = Depends(get_current_identity)):
    return {
        "email": identity["email"],
        "auth_source": identity["source"],
        "claims": identity["payload"],
    }
