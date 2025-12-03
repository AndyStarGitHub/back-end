from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, get_current_user, get_quiz_service
from app.services.quiz import QuizService

from app.schemas.quiz_analytics import (
    CompanyWeeklyStats,
    CompanyUserQuizWeeklyStats,
    CompanyUsersLastAttemptList,
)

router = APIRouter()


@router.get("/weekly", response_model=CompanyWeeklyStats)
async def get_company_weekly_stats(
    company_id: UUID,
    start: datetime | None = None,
    end: datetime | None = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    quiz_service: QuizService = Depends(get_quiz_service),
):

    return await quiz_service.get_company_weekly_stats(
        db,
        company_id=company_id,
        current_user=current_user,
        start=start,
        end=end,
    )


@router.get(
    "/users/{user_id}/weekly",
    response_model=CompanyUserQuizWeeklyStats,
)
async def get_company_user_quiz_weekly_stats(
    company_id: UUID,
    user_id: int,
    start: datetime | None = None,
    end: datetime | None = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    quiz_service: QuizService = Depends(get_quiz_service),
):

    return await quiz_service.get_company_user_quiz_weekly_stats(
        db,
        company_id=company_id,
        current_user=current_user,
        target_user_id=user_id,
        start=start,
        end=end,
    )


@router.get(
    "/users/last-attempts",
    response_model=CompanyUsersLastAttemptList,
)
async def get_company_users_last_attempts(
    company_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    quiz_service: QuizService = Depends(get_quiz_service),
):

    return await quiz_service.get_company_users_last_attempts(
        db,
        company_id=company_id,
        current_user=current_user,
    )
