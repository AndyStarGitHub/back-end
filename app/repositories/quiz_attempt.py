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
    ) -> tuple[int, int, datetime | None]:

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

        return total_q, total_correct, last_attempt_at

    async def get_user_stats_global(
        self,
        db: AsyncSession,
        *,
        user_id: int,
    ) -> tuple[int, int, datetime | None]:

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

        return total_q, total_correct, last_attempt_at

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

    async def get_user_quiz_aggregates_in_range(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        start: datetime | None = None,
        end: datetime | None = None,
        company_id: UUID | None = None,
    ) -> list[tuple[UUID, UUID, int, int, int]]:

        conditions = [QuizAttempt.user_id == user_id]

        if company_id is not None:
            conditions.append(QuizAttempt.company_id == company_id)

        if start is not None:
            conditions.append(QuizAttempt.created_at >= start)

        if end is not None:
            conditions.append(QuizAttempt.created_at <= end)

        stmt = (
            select(
                QuizAttempt.quiz_id,
                QuizAttempt.company_id,
                func.coalesce(func.sum(QuizAttempt.total_questions), 0),
                func.coalesce(func.sum(QuizAttempt.correct_answers), 0),
                func.count(QuizAttempt.id),
            )
            .where(*conditions)
            .group_by(QuizAttempt.quiz_id, QuizAttempt.company_id)
        )

        result = await db.execute(stmt)
        rows = result.all()
        return rows

    async def get_user_quiz_last_attempts(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        company_id: UUID | None = None,
    ) -> list[tuple[UUID, UUID, datetime | None]]:

        conditions = [QuizAttempt.user_id == user_id]

        if company_id is not None:
            conditions.append(QuizAttempt.company_id == company_id)

        stmt = (
            select(
                QuizAttempt.quiz_id,
                QuizAttempt.company_id,
                func.max(QuizAttempt.created_at),
            )
            .where(*conditions)
            .group_by(QuizAttempt.quiz_id, QuizAttempt.company_id)
        )

        result = await db.execute(stmt)
        rows = result.all()
        return rows

    async def get_company_weekly_aggregates(
        self,
        db: AsyncSession,
        *,
        company_id: UUID,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> list[tuple[datetime, int, int, int]]:

        week_expr = func.date_trunc("week", QuizAttempt.created_at)

        conditions = [QuizAttempt.company_id == company_id]

        if start is not None:
            conditions.append(QuizAttempt.created_at >= start)

        if end is not None:
            conditions.append(QuizAttempt.created_at <= end)

        stmt = (
            select(
                week_expr.label("week_start"),
                func.coalesce(func.sum(QuizAttempt.total_questions), 0),
                func.coalesce(func.sum(QuizAttempt.correct_answers), 0),
                func.count(QuizAttempt.id),
            )
            .where(*conditions)
            .group_by(week_expr)
            .order_by(week_expr.asc())
        )

        result = await db.execute(stmt)
        rows = result.all()
        return rows

    async def get_company_user_quiz_weekly_aggregates(
        self,
        db: AsyncSession,
        *,
        company_id: UUID,
        user_id: int,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> list[tuple[UUID, datetime, int, int, int]]:

        week_expr = func.date_trunc("week", QuizAttempt.created_at)

        conditions = [
            QuizAttempt.company_id == company_id,
            QuizAttempt.user_id == user_id,
        ]

        if start is not None:
            conditions.append(QuizAttempt.created_at >= start)

        if end is not None:
            conditions.append(QuizAttempt.created_at <= end)

        stmt = (
            select(
                QuizAttempt.quiz_id,
                week_expr.label("week_start"),
                func.coalesce(func.sum(QuizAttempt.total_questions), 0),
                func.coalesce(func.sum(QuizAttempt.correct_answers), 0),
                func.count(QuizAttempt.id),
            )
            .where(*conditions)
            .group_by(QuizAttempt.quiz_id, week_expr)
            .order_by(week_expr.asc())
        )

        result = await db.execute(stmt)
        rows = result.all()
        return rows

    async def get_company_users_last_attempts(
        self,
        db: AsyncSession,
        *,
        company_id: UUID,
    ) -> list[tuple[int, datetime | None]]:

        stmt = (
            select(
                QuizAttempt.user_id,
                func.max(QuizAttempt.created_at),
            )
            .where(QuizAttempt.company_id == company_id)
            .group_by(QuizAttempt.user_id)
        )

        result = await db.execute(stmt)
        rows = result.all()
        return rows
