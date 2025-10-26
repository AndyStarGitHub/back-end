from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional


class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool = True


class UserOut(UserBase):
    id: int


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
    password: Optional[str] = Field(default=None, min_length=6)


class UsersListResponse(BaseModel):
    total: int
    items: List[UserOut]


class UserDetailResponse(UserOut):
    pass
