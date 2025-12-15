from typing import List, Optional
from pydantic import BaseModel
from uuid import UUID


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
