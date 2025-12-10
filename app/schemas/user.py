from datetime import datetime

from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    ConfigDict,
)
from typing import List, Optional


class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool = True


class UserOut(BaseModel):
    id: int
    email: str
    full_name: str | None = None
    is_active: bool
    about: str | None = None
    phone: str | None = None
    position: str | None = None
    avatar_url: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


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
    about: Optional[str] = None
    phone: Optional[str] = None
    position: Optional[str] = None
    avatar_url: Optional[str] = None


class UsersListResponse(BaseModel):
    total: int
    items: List[UserOut]


class UserDetailResponse(UserOut):
    pass


class UserSelfUpdate(BaseModel):
    full_name: Optional[str] = Field(None, max_length=255)
    about: Optional[str] = None
    phone: Optional[str] = Field(None, max_length=32)
    position: Optional[str] = Field(None, max_length=255)
    avatar_url: Optional[str] = Field(None, max_length=512)


class UserPasswordChange(BaseModel):
    old_password: str = Field(..., min_length=6)
    new_password: str = Field(..., min_length=6)
