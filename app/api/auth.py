from loguru import logger
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.schemas.auth import TokenResponse, LoginRequest
from app.schemas.user import UserOut
from app.services.auth_service import AuthService

router = APIRouter()


def auth_service_dep(db: AsyncSession = Depends(get_db)) -> AuthService:
    return AuthService(db=db)


class SignInPayload(BaseModel):
    email: EmailStr
    password: str


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK
)
async def login(
        payload: LoginRequest,
        svc: AuthService = Depends(auth_service_dep)
):
    logger.info("Logit started:", payload.email)
    return await svc.login_with_password(
        email=payload.email,
        password=payload.password
    )


@router.get("/me", response_model=UserOut)
async def me(current_user: User = Depends(get_current_user)):
    return current_user


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/refresh")
async def refresh_token_endpoint(
    body: RefreshRequest,
    svc: AuthService = Depends(auth_service_dep),
):
    return await svc.refresh_access_token(
        refresh_token=body.refresh_token
    )
