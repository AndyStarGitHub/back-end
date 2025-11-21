from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.company_members import CompanyMemberUser
from app.services.company_members import (
    list_company_members,
    remove_member_from_company,
    leave_company,
)

router = APIRouter()


@router.get(
    "/{company_id}/members",
    response_model=List[CompanyMemberUser],
)
async def get_company_members(
    company_id: str,
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    users = await list_company_members(
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
    company_id: str,
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await remove_member_from_company(
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
    company_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    await leave_company(
        db=db,
        company_id=company_id,
        current_user=current_user,
    )
