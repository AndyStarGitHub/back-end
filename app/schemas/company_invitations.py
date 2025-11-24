from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class CompanyInvitationBase(BaseModel):
    status: str
    company_id: UUID          # замість str
    invited_user_id: int
    invited_by_id: int


class CompanyInvitationCreate(BaseModel):
    invited_user_id: int


class CompanyInvitationRead(CompanyInvitationBase):
    id: UUID                  # замість str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
