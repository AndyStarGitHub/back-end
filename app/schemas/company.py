from __future__ import annotations

from uuid import UUID
from enum import Enum

from pydantic import BaseModel, ConfigDict


class CompanyVisibility(str, Enum):
    hidden = "hidden"
    public = "public"


class CompanyBase(BaseModel):
    name: str
    description: str | None = None


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    visibility: CompanyVisibility | None = None


class CompanyRead(BaseModel):
    id: UUID
    owner_id: int
    name: str
    description: str | None
    visibility: CompanyVisibility

    model_config = ConfigDict(from_attributes=True)


class CompanyListResponse(BaseModel):
    total: int
    items: list[CompanyRead]
    offset: int
    limit: int
