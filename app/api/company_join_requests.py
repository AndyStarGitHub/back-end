from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.company_join_requests import (
    CompanyJoinRequestCreate,
    CompanyJoinRequestRead,
)
from app.services.company_join_requests import (
    create_join_request,
    cancel_join_request,
    approve_join_request,
    reject_join_request,
    list_my_join_requests,
    list_company_join_requests,
)

router = APIRouter()


@router.post(
    "/companies/{company_id}",
    response_model=CompanyJoinRequestRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_company_join_request(
    company_id: str,
    _: CompanyJoinRequestCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    join_request = await create_join_request(
        db=db,
        company_id=company_id,
        current_user=current_user,
    )
    return join_request


@router.post(
    "/{join_request_id}/cancel",
    response_model=CompanyJoinRequestRead,
)
async def cancel_company_join_request(
    join_request_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    join_request = await cancel_join_request(
        db=db,
        join_request_id=join_request_id,
        current_user=current_user,
    )
    return join_request


@router.post(
    "/{join_request_id}/approve",
    response_model=CompanyJoinRequestRead,
)
async def approve_company_join_request(
    join_request_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    join_request = await approve_join_request(
        db=db,
        join_request_id=join_request_id,
        current_user=current_user,
    )
    return join_request


@router.post(
    "/{join_request_id}/reject",
    response_model=CompanyJoinRequestRead,
)
async def reject_company_join_request(
    join_request_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    join_request = await reject_join_request(
        db=db,
        join_request_id=join_request_id,
        current_user=current_user,
    )
    return join_request


@router.get(
    "/me",
    response_model=List[CompanyJoinRequestRead],
)
async def get_my_join_requests(
    status_filter: str | None = None,
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    join_requests = await list_my_join_requests(
        db=db,
        current_user=current_user,
        status=status_filter,
        limit=limit,
        offset=offset,
    )
    return join_requests


@router.get(
    "/companies/{company_id}",
    response_model=List[CompanyJoinRequestRead],
)
async def get_company_join_requests(
    company_id: str,
    status_filter: str | None = None,
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    join_requests = await list_company_join_requests(
        db=db,
        company_id=company_id,
        current_user=current_user,
        status=status_filter,
        limit=limit,
        offset=offset,
    )
    return join_requests
