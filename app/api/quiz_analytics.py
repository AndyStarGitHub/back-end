from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, get_current_user, get_quiz_service
from app.services.quiz import QuizService


from app.schemas.quiz import UserQuizStats
from app.schemas.quiz_analytics import (
    UserQuizAverageList,
    UserQuizLastAttemptList,
)

router = APIRouter()


@router.get("/overall-rating", response_model=UserQuizStats)
async def get_my_overall_rating(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    quiz_service: QuizService = Depends(get_quiz_service),
):

    return await quiz_service.get_user_overall_rating(
        db,
        current_user=current_user,
    )


@router.get("/averages", response_model=UserQuizAverageList)
async def get_my_quiz_averages(
    start: datetime | None = None,
    end: datetime | None = None,
    company_id: UUID | None = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    quiz_service: QuizService = Depends(get_quiz_service),
):

    return await quiz_service.get_user_quiz_average_scores(
        db,
        current_user=current_user,
        start=start,
        end=end,
        company_id=company_id,
    )


@router.get("/last-attempts", response_model=UserQuizLastAttemptList)
async def get_my_quiz_last_attempts(
    company_id: UUID | None = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    quiz_service: QuizService = Depends(get_quiz_service),
):

    return await quiz_service.get_user_quiz_last_attempts(
        db,
        current_user=current_user,
        company_id=company_id,
    )
