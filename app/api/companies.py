from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, get_current_user
from app.models import User
from app.services import company_admin_service
from app.services.company import CompanyService
from app.schemas.company import (
    CompanyCreate,
    CompanyUpdate,
    CompanyRead,
    CompanyListResponse,
    CompanyAdminOut,
)


router = APIRouter()

service = CompanyService()


@router.post(
    "",
    response_model=CompanyRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_company(
    data: CompanyCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
) -> CompanyRead:
    return await service.create_company(
        db,
        current_user=current_user,
        data=data,
    )


@router.get(
    "",
    response_model=CompanyListResponse,
)
async def list_companies(
    db: AsyncSession = Depends(get_db),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> CompanyListResponse:
    return await service.list_public_companies(
        db,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/me",
    response_model=CompanyListResponse,
)
async def list_my_companies(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> CompanyListResponse:
    return await service.list_my_companies(
        db,
        current_user=current_user,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/{company_id}",
    response_model=CompanyRead,
)
async def get_company(
    company_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
) -> CompanyRead:
    return await service.get_company(
        db,
        company_id=company_id,
        current_user=current_user,
    )


@router.patch(
    "/{company_id}",
    response_model=CompanyRead,
)
async def update_company(
    company_id: UUID,
    data: CompanyUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
) -> CompanyRead:
    return await service.update_company(
        db,
        company_id=company_id,
        current_user=current_user,
        data=data,
    )


@router.delete(
    "/{company_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_company(
    company_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
) -> None:
    await service.delete_company(
        db,
        company_id=company_id,
        current_user=current_user,
    )


@router.get(
    "/{company_id}/admins",
    response_model=list[CompanyAdminOut],
)
async def get_company_admins(
    company_id: str,  # або UUID
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    admins = await company_admin_service.list_admins(
        db,
        company_id=company_id,
        current_user=current_user,
    )
    return admins


@router.post("/{company_id}/admins/{user_id}", status_code=204)
async def make_user_admin(
    company_id: str,
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await company_admin_service.assign_admin(
        db,
        company_id=company_id,
        member_user_id=user_id,
        current_user=current_user,
    )
    return


@router.delete("/{company_id}/admins/{user_id}", status_code=204)
async def remove_user_admin(
    company_id: str,
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await company_admin_service.remove_admin(
        db,
        company_id=company_id,
        member_user_id=user_id,
        current_user=current_user,
    )
    return
