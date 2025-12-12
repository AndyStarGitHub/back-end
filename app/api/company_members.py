from __future__ import annotations

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.company_members import (
    CompanyMemberUser,
    MyMembershipsResponse
)
from app.services.company_members import member_service


router = APIRouter()


@router.get(
    "/{company_id}/members",
    response_model=List[CompanyMemberUser],
)
async def get_company_members(
    company_id: UUID,
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    users = await member_service.list_company_members(
        db=db,
        company_id=company_id,
        limit=limit,
        offset=offset,
    )
    return users


@router.delete(
    "/{company_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_company_member(
    company_id: UUID,
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await member_service.remove_member_from_company(
        db=db,
        company_id=company_id,
        member_user_id=user_id,
        current_user=current_user,
    )


@router.post(
    "/{company_id}/leave",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def leave_company_endpoint(
    company_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await member_service.leave_company(
        db=db,
        company_id=company_id,
        current_user=current_user,
    )


@router.get(
    "/me",
    response_model=MyMembershipsResponse,
)
async def get_my_memberships(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await member_service.list_my_memberships(
        db=db,
        current_user=current_user,
        limit=limit,
        offset=offset,
    )
