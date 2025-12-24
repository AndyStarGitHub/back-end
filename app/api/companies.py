from __future__ import annotations

from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, get_current_user

from app.models import User
from app.schemas.company_members import CompanyMemberRead
from app.services import company_admin_service
from app.services.company import CompanyService
from app.services.quiz import QuizService
from app.schemas.company import (
    CompanyCreate,
    CompanyUpdate,
    CompanyRead,
    CompanyListResponse,
    CompanyAdminOut,
)
from app.schemas.quiz import (
    QuizCreate,
    QuizUpdate,
    QuizRead,
    QuizListResponse,
    QuizAttemptRead,
    UserQuizStats,
    QuizSubmit,
)


ExportFormat = Literal["json", "csv"]

router = APIRouter()

service = CompanyService()
quiz_service = QuizService()


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
    company_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    admins = await company_admin_service.list_admins(
        db,
        company_id=company_id,
        current_user=current_user,
    )
    return admins


@router.post(
    "/{company_id}/admins/{user_id}",
    response_model=CompanyMemberRead,
    status_code=status.HTTP_200_OK,
)
async def make_user_admin(
    company_id: UUID,
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CompanyAdminOut:
    member = await company_admin_service.assign_admin(
        db,
        company_id=company_id,
        member_user_id=user_id,
        current_user=current_user,
    )
    return member


@router.delete(
    "/{company_id}/admins/{user_id}",
    response_model=CompanyMemberRead,
    status_code=status.HTTP_200_OK,
)
async def remove_user_admin(
    company_id: UUID,
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CompanyMemberRead:
    member = await company_admin_service.remove_admin(
        db,
        company_id=company_id,
        member_user_id=user_id,
        current_user=current_user,
    )
    return member


@router.post(
    "/{company_id}/quizzes",
    response_model=QuizRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_quiz_for_company(
    company_id: UUID,
    data: QuizCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> QuizRead:
    return await quiz_service.create_quiz(
        db,
        company_id=company_id,
        current_user=current_user,
        data=data,
    )


@router.get(
    "/{company_id}/quizzes",
    response_model=QuizListResponse,
)
async def list_company_quizzes(
    company_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> QuizListResponse:
    return await quiz_service.list_quizzes_for_company(
        db,
        company_id=company_id,
        current_user=current_user,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/{company_id}/quizzes/{quiz_id}",
    response_model=QuizRead,
)
async def get_company_quiz(
    company_id: UUID,
    quiz_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> QuizRead:
    return await quiz_service.get_quiz(
        db,
        company_id=company_id,
        quiz_id=quiz_id,
        current_user=current_user,
    )


@router.patch(
    "/{company_id}/quizzes/{quiz_id}",
    response_model=QuizRead,
)
async def update_company_quiz(
    company_id: UUID,
    quiz_id: UUID,
    data: QuizUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> QuizRead:
    return await quiz_service.update_quiz(
        db,
        company_id=company_id,
        quiz_id=quiz_id,
        current_user=current_user,
        data=data,
    )


@router.delete(
    "/{company_id}/quizzes/{quiz_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_company_quiz(
    company_id: UUID,
    quiz_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    await quiz_service.delete_quiz(
        db,
        company_id=company_id,
        quiz_id=quiz_id,
        current_user=current_user,
    )


@router.post(
    "/{company_id}/quizzes/{quiz_id}/attempts",
    response_model=QuizAttemptRead,
)
async def submit_quiz_attempt(
    company_id: UUID,
    quiz_id: UUID,
    data: QuizSubmit,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> QuizAttemptRead:
    return await quiz_service.submit_quiz(
        db,
        company_id=company_id,
        quiz_id=quiz_id,
        current_user=current_user,
        data=data,
    )


@router.get(
    "/{company_id}/me/quiz-stats",
    response_model=UserQuizStats,
)
async def get_my_company_quiz_stats(
    company_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserQuizStats:
    return await quiz_service.get_user_stats_for_company(
        db,
        company_id=company_id,
        current_user=current_user,
    )


@router.get(
    "/me/quiz-stats",
    response_model=UserQuizStats,
)
async def get_my_global_quiz_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserQuizStats:
    return await quiz_service.get_user_stats_global(
        db,
        current_user=current_user,
    )
