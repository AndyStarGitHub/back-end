from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, get_quiz_service, optional_current_user_dep
from app.services.quiz import QuizService
from app.schemas.quiz_analytics import GlobalRatingStats

router = APIRouter()


@router.get("/general-rating", response_model=GlobalRatingStats)
async def get_general_rating(
    db: AsyncSession = Depends(get_db),
    quiz_service: QuizService = Depends(get_quiz_service),
    _user=Depends(optional_current_user_dep),
):
    return await quiz_service.get_global_rating_stats(db)
