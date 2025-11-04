from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.dependencies import get_current_user_auth0
from app.schemas.user import UserOut  # твій UserOut

router = APIRouter()

@router.get("/me", response_model=UserOut, tags=["auth0"])
async def me_auth0(
    user = Depends(get_current_user_auth0),
    db: AsyncSession = Depends(get_db),
):
    # просто повертаємо юзера (схема виведе email, id, created_at ...)
    return user
