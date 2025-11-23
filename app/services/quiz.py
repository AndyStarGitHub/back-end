from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFound, Forbidden, BadRequest
from app.models.company import Company
from app.models.company_member import CompanyMemberRoleEnum
from app.models.quiz import Quiz
from app.repositories.company import CompanyRepository
from app.repositories.company_member import CompanyMemberRepository
from app.repositories.quiz import QuizRepository
from app.schemas.quiz import (
    QuizCreate,
    QuizUpdate,
    QuizRead,
    QuizListResponse,
    QuizQuestionCreate,
)


class QuizService:
    def __init__(
        self,
        quiz_repo: QuizRepository | None = None,
        company_repo: CompanyRepository | None = None,
        company_member_repo: CompanyMemberRepository | None = None,
    ) -> None:
        self.quiz_repo = quiz_repo or QuizRepository()
        self.company_repo = company_repo or CompanyRepository()
        self.company_member_repo = (company_member_repo
                                    or
                                    CompanyMemberRepository())

    async def _get_company_or_404(
        self,
        db: AsyncSession,
        company_id: UUID,
    ) -> Company:
        company = await self.company_repo.get_by_id(db, company_id)
        if company is None:
            raise NotFound("Company not found")
        return company

    async def _ensure_is_company_admin(
        self,
        db: AsyncSession,
        *,
        company: Company,
        current_user: Any,
    ) -> None:

        if company.owner_id == current_user.id:
            return

        member = await self.company_member_repo.get_one_for_company_and_user(
            db,
            company_id=company.id,
            user_id=current_user.id,
        )
        if not member or member.role != CompanyMemberRoleEnum.ADMIN:
            raise Forbidden("Only company owner or admin can manage quizzes")

    def _validate_questions(self, questions: list[QuizQuestionCreate]) -> None:

        if len(questions) < 2:
            raise NotFound("Quiz must contain at least two questions")

        for qu in questions:
            if len(qu.options) < 2:
                raise NotFound(
                    "Each question must have at least two answer options"
                )
            if len(qu.options) > 4:
                raise NotFound(
                    "Each question can have at most four answer options"
                )
            if not any(o.is_correct for o in qu.options):
                raise NotFound(
                    "Each question must have at least one correct answer"
                )

    async def _get_quiz_or_404(
        self,
        db: AsyncSession,
        quiz_id: UUID,
    ) -> Quiz:
        quiz = await self.quiz_repo.get_full_by_id(db, quiz_id)
        if quiz is None:
            raise NotFound("Quiz not found")
        return quiz

    async def create_quiz(
        self,
        db: AsyncSession,
        *,
        company_id: UUID,
        current_user: Any,
        data: QuizCreate,
    ) -> QuizRead:

        company = await self._get_company_or_404(db, company_id)
        await self._ensure_is_company_admin(
            db,
            company=company,
            current_user=current_user,
        )

        self._validate_questions(data.questions)

        quiz = await self.quiz_repo.create_with_nested(
            db,
            company_id=company_id,
            data=data,
        )

        return QuizRead.model_validate(quiz)

    async def get_quiz(
        self,
        db: AsyncSession,
        *,
        company_id: UUID,
        quiz_id: UUID,
        current_user: Any,
    ) -> QuizRead:

        company = await self._get_company_or_404(db, company_id)
        await self._ensure_is_company_admin(
            db,
            company=company,
            current_user=current_user,
        )

        quiz = await self._get_quiz_or_404(db, quiz_id)

        if quiz.company_id != company_id:
            raise NotFound("Quiz not found")

        return QuizRead.model_validate(quiz)

    async def update_quiz(
        self,
        db: AsyncSession,
        *,
        company_id: UUID,
        quiz_id: UUID,
        current_user: Any,
        data: QuizUpdate,
    ) -> QuizRead:

        company = await self._get_company_or_404(db, company_id)
        await self._ensure_is_company_admin(
            db,
            company=company,
            current_user=current_user,
        )

        quiz = await self._get_quiz_or_404(db, quiz_id)
        if quiz.company_id != company_id:
            raise NotFound("Quiz not found")

        if data.questions is not None:
            self._validate_questions(data.questions)

        quiz = await self.quiz_repo.update_with_nested(
            db,
            quiz=quiz,
            data=data,
        )

        return QuizRead.model_validate(quiz)

    async def delete_quiz(
        self,
        db: AsyncSession,
        *,
        company_id: UUID,
        quiz_id: UUID,
        current_user: Any,
    ) -> None:

        company = await self._get_company_or_404(db, company_id)
        await self._ensure_is_company_admin(
            db,
            company=company,
            current_user=current_user,
        )

        quiz = await self._get_quiz_or_404(db, quiz_id)
        if quiz.company_id != company_id:
            raise NotFound("Quiz not found")

        await self.quiz_repo.delete_quiz(db, quiz=quiz)

    async def list_quizzes_for_company(
        self,
        db: AsyncSession,
        *,
        company_id: UUID,
        current_user: Any,
        offset: int = 0,
        limit: int = 50,
    ) -> QuizListResponse:

        company = await self._get_company_or_404(db, company_id)
        await self._ensure_is_company_admin(
            db,
            company=company,
            current_user=current_user,
        )

        total, items = await self.quiz_repo.get_paginated_full_for_company(
            db,
            company_id=company_id,
            offset=offset,
            limit=limit,
        )

        return QuizListResponse(
            total=total,
            items=[QuizRead.model_validate(q) for q in items],
            offset=offset,
            limit=limit,
        )
