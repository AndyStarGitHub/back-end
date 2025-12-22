from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class CompanyInvitationBase(BaseModel):
    status: str
    company_id: UUID
    invited_user_id: int
    invited_by_id: int


class CompanyInvitationCreate(BaseModel):
    invited_user_id: int


class CompanyInvitationRead(CompanyInvitationBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    company_name: str

    class Config:
        from_attributes = True
