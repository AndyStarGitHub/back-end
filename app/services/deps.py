from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import optional_current_user_dep
from app.db.database import get_db
from app.models import User
from app.services.user_service import UserService


def get_user_service(
        db: AsyncSession = Depends(get_db)
) -> UserService:
    return UserService(db)

def user_service_dep(
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(optional_current_user_dep),
) -> UserService:
    """
    Повертає інстанс UserService з прокинутими db і (опційно) current_user.
    Якщо потрібно ЗАВЖДИ вимагати авторизацію — заміни optional_current_user_dep на get_current_user_auth0.
    """
    return UserService(db=db, current_user=current_user)
