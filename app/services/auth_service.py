from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.user_repo import user_repo
from app.core.errors import InvalidCredentials, InactiveUser
from app.core.security import verify_password
from app.core.jwt import create_access_token  # ми оновимо його пізніше, поки використовуй поточний
from app.models.user import User


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def login_with_password(self, *, email: str, password: str) -> dict:
        user: User | None = await user_repo.get_by_email(self.db, email)
        if not user or not verify_password(password, user.hashed_password):
            raise InvalidCredentials("Invalid credentials")

        if getattr(user, "is_active", True) is False:
            raise InactiveUser()

        if not verify_password(password, user.hashed_password):
            raise InvalidCredentials()

        # поки що як було: sub = user.id, email у payload (пізніше зробимо "email обов’язковим")
        access_token = create_access_token(sub=str(user.id), email=user.email)
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user,
        }
