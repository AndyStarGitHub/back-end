from fastapi import APIRouter, Depends
from app.core.deps import get_current_user_auth0
from app.models.user import User
from app.schemas.user import UserOut


router = APIRouter()


@router.post("/touch", response_model=UserOut, tags=["auth0"])
async def auth0_touch(me: User = Depends(get_current_user_auth0)):
    return me
