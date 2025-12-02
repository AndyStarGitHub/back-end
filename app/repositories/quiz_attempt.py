from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID
from typing import Sequence


from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.quiz_attempt import (
    QuizAttempt,
    QuizAttemptAnswer,
    QuizAttemptAnswerOption,
)
from app.repositories.base import BaseRepository


@dataclass
class QuizAttemptAnswerData:
    question_id: UUID
    is_correct: bool
    selected_option_ids: list[UUID]


@dataclass
class UserQuizStatsData:
    total_questions_answered: int
    total_correct_answers: int
    last_attempt_at: datetime | None


class QuizAttemptRepository(BaseRepository[QuizAttempt]):
    def __init__(self) -> None:
        super().__init__(QuizAttempt)

    async def get_full_by_id(
        self,
        db: AsyncSession,
        attempt_id: UUID,
    ) -> QuizAttempt | None:

        result = await db.execute(
            select(QuizAttempt)
            .where(QuizAttempt.id == attempt_id)
            .options(
                selectinload(QuizAttempt.answers)
                .selectinload(QuizAttemptAnswer.selected_options)
                .selectinload(QuizAttemptAnswerOption.option)
            )
        )
        return result.scalars().first()

    async def create_attempt_with_answers(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        company_id: UUID,
        quiz_id: UUID,
        total_questions: int,
        correct_answers: int,
        answers: list[QuizAttemptAnswerData],
    ) -> QuizAttempt:

        attempt = QuizAttempt(
            user_id=user_id,
            company_id=company_id,
            quiz_id=quiz_id,
            total_questions=total_questions,
            correct_answers=correct_answers,
        )

        for ans_data in answers:
            answer = QuizAttemptAnswer(
                question_id=ans_data.question_id,
                is_correct=ans_data.is_correct,
            )

            for option_id in ans_data.selected_option_ids:
                answer_option = QuizAttemptAnswerOption(
                    option_id=option_id,
                )
                answer.selected_options.append(answer_option)

            attempt.answers.append(answer)

        db.add(attempt)
        await db.commit()

        refreshed = await self.get_full_by_id(db, attempt.id)
        return refreshed or attempt

    async def get_user_stats_for_company(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        company_id: UUID,
    ) -> UserQuizStatsData:

        result = await db.execute(
            select(
                func.coalesce(func.sum(QuizAttempt.total_questions), 0),
                func.coalesce(func.sum(QuizAttempt.correct_answers), 0),
                func.max(QuizAttempt.created_at),
            ).where(
                QuizAttempt.user_id == user_id,
                QuizAttempt.company_id == company_id,
            )
        )
        total_q, total_correct, last_attempt_at = result.one()

        return UserQuizStatsData(
            total_questions_answered=int(total_q or 0),
            total_correct_answers=int(total_correct or 0),
            last_attempt_at=last_attempt_at,
        )

    async def get_user_stats_global(
        self,
        db: AsyncSession,
        *,
        user_id: int,
    ) -> UserQuizStatsData:

        result = await db.execute(
            select(
                func.coalesce(func.sum(QuizAttempt.total_questions), 0),
                func.coalesce(func.sum(QuizAttempt.correct_answers), 0),
                func.max(QuizAttempt.created_at),
            ).where(
                QuizAttempt.user_id == user_id,
            )
        )
        total_q, total_correct, last_attempt_at = result.one()

        return UserQuizStatsData(
            total_questions_answered=int(total_q or 0),
            total_correct_answers=int(total_correct or 0),
            last_attempt_at=last_attempt_at,
        )

    async def get_attempts_for_company_and_user(
        self,
        db: AsyncSession,
        *,
        company_id: UUID,
        user_id: int,
        since: datetime | None = None,
        quiz_id: UUID | None = None,
    ) -> Sequence[QuizAttempt]:

        conditions = [
            QuizAttempt.company_id == company_id,
            QuizAttempt.user_id == user_id,
        ]

        if quiz_id is not None:
            conditions.append(QuizAttempt.quiz_id == quiz_id)

        if since is not None:
            conditions.append(QuizAttempt.created_at >= since)

        stmt = (
            select(QuizAttempt)
            .where(and_(*conditions))
            .order_by(QuizAttempt.created_at.desc())
        )

        result = await db.execute(stmt)
        return result.scalars().all()

    async def get_attempts_for_company(
        self,
        db: AsyncSession,
        *,
        company_id: UUID,
        since: datetime | None = None,
        quiz_id: UUID | None = None,
    ) -> Sequence[QuizAttempt]:

        conditions = [QuizAttempt.company_id == company_id]

        if quiz_id is not None:
            conditions.append(QuizAttempt.quiz_id == quiz_id)

        if since is not None:
            conditions.append(QuizAttempt.created_at >= since)

        stmt = (
            select(QuizAttempt)
            .where(and_(*conditions))
            .order_by(QuizAttempt.created_at.desc())
        )

        result = await db.execute(stmt)
        return result.scalars().all()
