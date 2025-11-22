from __future__ import annotations

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.company_invitations import (
    CompanyInvitationCreate,
    CompanyInvitationRead,
)
from app.services.company_invitations import CompanyInvitationService

router = APIRouter()
invitation_service = CompanyInvitationService()


@router.post(
    "/companies/{company_id}",
    response_model=CompanyInvitationRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_company_invitation(
    company_id: UUID,
    data: CompanyInvitationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    invitation = await invitation_service.invite_user_to_company(
        db=db,
        company_id=company_id,
        invited_user_id=data.invited_user_id,
        current_user=current_user,
    )
    return invitation


@router.get(
    "/me",
    response_model=List[CompanyInvitationRead],
)
async def get_my_invitations(
    status_filter: str | None = None,
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    invitations = await invitation_service.list_my_invitations(
        db=db,
        current_user=current_user,
        status=status_filter,
        limit=limit,
        offset=offset,
    )
    return invitations


@router.get(
    "/companies/{company_id}",
    response_model=List[CompanyInvitationRead],
)
async def get_company_invitations(
    company_id: UUID,
    status_filter: str | None = None,
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    invitations = await invitation_service.list_company_invitations(
        db=db,
        company_id=company_id,
        current_user=current_user,
        status=status_filter,
        limit=limit,
        offset=offset,
    )
    return invitations


@router.post(
    "/{invitation_id}/accept",
    response_model=CompanyInvitationRead,
)
async def accept_company_invitation(
    invitation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    invitation = await invitation_service.accept_invitation(
        db=db,
        invitation_id=invitation_id,
        current_user=current_user,
    )
    return invitation


@router.post(
    "/{invitation_id}/decline",
    response_model=CompanyInvitationRead,
)
async def decline_company_invitation(
    invitation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    invitation = await invitation_service.decline_invitation(
        db=db,
        invitation_id=invitation_id,
        current_user=current_user,
    )
    return invitation


@router.post(
    "/{invitation_id}/cancel",
    response_model=CompanyInvitationRead,
)
async def cancel_company_invitation(
    invitation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    invitation = await invitation_service.cancel_invitation(
        db=db,
        invitation_id=invitation_id,
        current_user=current_user,
    )
    return invitation
