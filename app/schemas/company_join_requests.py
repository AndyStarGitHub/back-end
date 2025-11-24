from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class CompanyJoinRequestCreate(BaseModel):
    pass


class CompanyJoinRequestRead(BaseModel):
    id: UUID
    company_id: UUID
    user_id: int
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
