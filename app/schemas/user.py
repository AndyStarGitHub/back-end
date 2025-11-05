from datetime import datetime

from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    ConfigDict,
    field_serializer
)
from typing import List, Optional

from zoneinfo import ZoneInfo


class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool = True


class UserOut(BaseModel):
    id: int
    email: str
    full_name: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("created_at")
    def _serialize_created_at(self, dt: datetime, _info):
        if dt is None:
            return None
        kyiv = ZoneInfo("Europe/Kyiv")
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=kyiv)
        else:
            dt = dt.astimezone(kyiv)
        return dt.isoformat()


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    full_name: Optional[str] = None


class SignInRequest(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    is_active: Optional[bool] = None


class UsersListResponse(BaseModel):
    total: int
    items: List[UserOut]


class UserDetailResponse(UserOut):
    pass
