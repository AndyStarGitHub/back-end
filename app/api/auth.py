from loguru import logger
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_identity, get_current_user_auth0
from app.db.database import get_db
from app.models.user import User
from app.repositories import user_repo
from app.core.security import decode_token
from app.repositories.user_repo import user_repo
from app.schemas.auth import TokenResponse, LoginRequest
from app.schemas.user import UserOut
from app.services.auth_service import AuthService

router = APIRouter()


def auth_service_dep(db: AsyncSession = Depends(get_db)) -> AuthService:
    return AuthService(db=db)

class SignInPayload(BaseModel):
    email: EmailStr
    password: str


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def login(payload: LoginRequest, svc: AuthService = Depends(auth_service_dep)):
    logger.info("Logit started:", payload.email)
    # якщо креди невалідні — з сервісу полетить InvalidCredentials -> автоматом 401
    return await svc.login_with_password(email=payload.email, password=payload.password)





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
async def me(req: Request, identity=Depends(get_current_identity)):
    logger.info("AUTH HEADER RAW: {}", req.headers.get("authorization"))
    logger.info("identity: {}", identity)
    return identity


@router.get("/auth/debug-headers")
async def debug_headers(req: Request):
    from loguru import logger
    auth = req.headers.get("authorization")
    logger.info("DEBUG /auth/debug-headers, Authorization = {}", auth)
    return {"authorization": auth}

