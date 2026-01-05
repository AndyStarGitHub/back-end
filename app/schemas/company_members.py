from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime

from app.models.company_member import CompanyMemberRoleEnum


class CompanyMemberUser(BaseModel):
    id: int
    email: str

    class Config:
        from_attributes = True


class CompanyShort(BaseModel):
    id: UUID
    owner_id: int
    name: str
    description: Optional[str] = None
    visibility: str

    class Config:
        from_attributes = True


class CompanyMembershipOut(BaseModel):
    id: UUID
    role: str
    company: CompanyShort

    class Config:
        from_attributes = True


class MyMembershipsResponse(BaseModel):
    total: int
    items: List[CompanyMembershipOut]
    offset: int
    limit: int


class CompanyMemberRead(BaseModel):
    id: UUID
    company_id: UUID | str
    user_id: int
    role: CompanyMemberRoleEnum
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
