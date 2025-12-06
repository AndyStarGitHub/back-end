from __future__ import annotations

from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.quiz import Quiz, QuizQuestion, QuizAnswerOption
from app.repositories.base import BaseRepository
from app.schemas.quiz import QuizCreate, QuizUpdate


class QuizRepository(BaseRepository[Quiz]):
    def __init__(self) -> None:
        super().__init__(Quiz)

    async def get_all_for_company_simple(
        self,
        db: AsyncSession,
        *,
        company_id: UUID,
    ) -> list[Quiz]:

        res = await db.execute(
            select(Quiz).where(Quiz.company_id == company_id)
        )
        return list(res.scalars().all())

    async def get_full_by_id(
        self,
        db: AsyncSession,
        quiz_id: UUID,
    ) -> Quiz | None:

        result = await db.execute(
            select(Quiz)
                .where(Quiz.id == quiz_id)
                .options(
                    selectinload(Quiz.questions).selectinload(
                        QuizQuestion.options
                    )
                )
        )
        return result.scalars().first()

    async def get_paginated_full_for_company(
        self,
        db: AsyncSession,
        *,
        company_id: UUID,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[int, list[Quiz]]:

        total_result = await db.execute(
            select(func.count()).select_from(Quiz).where(
                Quiz.company_id == company_id,
            )
        )
        total = total_result.scalar_one()

        result = await db.execute(
            select(Quiz)
                .where(Quiz.company_id == company_id)
                .options(
                    selectinload(Quiz.questions).selectinload(
                        QuizQuestion.options
                    )
                )
                .offset(offset)
                .limit(limit)
        )
        items = list(result.scalars().all())
        return total, items

    async def create_with_nested(
        self,
        db: AsyncSession,
        *,
        company_id: UUID,
        data: QuizCreate,
    ) -> Quiz:

        quiz = Quiz(
            title=data.title,
            description=data.description,
            frequency=data.frequency.value,
            company_id=company_id,
        )

        for q_data in data.questions:
            question = QuizQuestion(title=q_data.title)
            for opt_data in q_data.options:
                option = QuizAnswerOption(
                    text=opt_data.text,
                    is_correct=opt_data.is_correct,
                )
                question.options.append(option)
            quiz.questions.append(question)

        db.add(quiz)
        await db.commit()

        refreshed = await self.get_full_by_id(db, quiz.id)

        return refreshed or quiz

    async def update_with_nested(
        self,
        db: AsyncSession,
        *,
        quiz: Quiz,
        data: QuizUpdate,
    ) -> Quiz:

        if data.title is not None:
            quiz.title = data.title
        if data.description is not None:
            quiz.description = data.description
        if data.frequency is not None:
            quiz.frequency = data.frequency.value

        if data.questions is not None:

            quiz.questions.clear()

            for q_data in data.questions:
                question = QuizQuestion(title=q_data.title)
                for opt_data in q_data.options:
                    option = QuizAnswerOption(
                        text=opt_data.text,
                        is_correct=opt_data.is_correct,
                    )
                    question.options.append(option)
                quiz.questions.append(question)

        await db.commit()

        refreshed = await self.get_full_by_id(db, quiz.id)
        return refreshed or quiz

    async def delete_quiz(
        self,
        db: AsyncSession,
        *,
        quiz: Quiz,
    ) -> None:

        await db.delete(quiz)
        await db.commit()
