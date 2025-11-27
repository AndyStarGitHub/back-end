from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFound, Forbidden
from app.models.company import Company
from app.models.company_member import CompanyMemberRoleEnum
from app.models.quiz import Quiz
from app.repositories.company import CompanyRepository
from app.repositories.company_member import CompanyMemberRepository
from app.repositories.quiz import QuizRepository
from app.repositories.quiz_attempt import (
    QuizAttemptRepository,
    QuizAttemptAnswerData,
    UserQuizStatsData,
)
from app.schemas.quiz import (
    QuizCreate,
    QuizUpdate,
    QuizRead,
    QuizListResponse,
    QuizQuestionCreate,
    QuizSubmit,
    QuizAttemptRead,
    UserQuizStats,
)

from app.repositories.quiz_redis import QuizRedisRepository


class QuizService:
    def __init__(
        self,
        quiz_repo: QuizRepository | None = None,
        company_repo: CompanyRepository | None = None,
        company_member_repo: CompanyMemberRepository | None = None,
        quiz_attempt_repo: QuizAttemptRepository | None = None,
        quiz_redis_repo: QuizRedisRepository | None = None,
    ) -> None:
        self.quiz_repo = quiz_repo or QuizRepository()
        self.company_repo = company_repo or CompanyRepository()
        self.company_member_repo = (
            company_member_repo or CompanyMemberRepository()
        )
        self.quiz_attempt_repo = quiz_attempt_repo or QuizAttemptRepository()
        self.quiz_redis_repo = quiz_redis_repo

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

    def _prepare_attempt_data(
        self,
        quiz: Quiz,
        submit: QuizSubmit,
    ) -> tuple[int, int, list[QuizAttemptAnswerData]]:

        if not quiz.questions:
            raise NotFound("Quiz has no questions")

        question_ids = {q.id for q in quiz.questions}

        correct_options_by_question: dict[UUID, set[UUID]] = {}
        options_by_question: dict[UUID, set[UUID]] = {}

        for qu in quiz.questions:
            q_option_ids = {opt.id for opt in qu.options}
            options_by_question[qu.id] = q_option_ids
            correct_options_by_question[qu.id] = {
                opt.id for opt in qu.options if opt.is_correct
            }

        submitted_question_ids = {a.question_id for a in submit.answers}

        if submitted_question_ids != question_ids:
            raise NotFound("You must answer all questions exactly once")

        answer_data_list: list[QuizAttemptAnswerData] = []
        total_questions = 0
        correct_answers = 0

        for ans in submit.answers:
            if ans.question_id not in question_ids:
                raise NotFound("Answer refers to a question not in this quiz")

            if not ans.selected_option_ids:
                raise NotFound(
                    "Each question must have at least one selected option"
                )

            selected_set = set(ans.selected_option_ids)

            allowed_options = options_by_question[ans.question_id]
            if not selected_set.issubset(allowed_options):
                raise NotFound(
                    "Selected option does not belong to this question"
                )

            correct_set = correct_options_by_question[ans.question_id]
            is_correct = selected_set == correct_set

            total_questions += 1
            if is_correct:
                correct_answers += 1

            answer_data_list.append(
                QuizAttemptAnswerData(
                    question_id=ans.question_id,
                    is_correct=is_correct,
                    selected_option_ids=list(selected_set),
                )
            )

        return total_questions, correct_answers, answer_data_list

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

    async def submit_quiz(
        self,
        db: AsyncSession,
        *,
        company_id: UUID,
        quiz_id: UUID,
        current_user: Any,
        data: QuizSubmit,
    ) -> QuizAttemptRead:

        company = await self._get_company_or_404(db, company_id)

        quiz = await self._get_quiz_or_404(db, quiz_id)
        if quiz.company_id != company_id:
            raise NotFound("Quiz not found")

        total_questions, correct_answers, answers_data = (
            self._prepare_attempt_data(quiz, data)
        )

        attempt = await self.quiz_attempt_repo.create_attempt_with_answers(
            db,
            user_id=current_user.id,
            company_id=company.id,
            quiz_id=quiz.id,
            total_questions=total_questions,
            correct_answers=correct_answers,
            answers=answers_data,
        )

        if self.quiz_redis_repo is not None:
            try:
                await self.quiz_redis_repo.save_attempt(attempt)
            except Exception:
                pass

        return QuizAttemptRead.model_validate(attempt)

    async def get_user_stats_for_company(
        self,
        db: AsyncSession,
        *,
        company_id: UUID,
        current_user: Any,
    ) -> UserQuizStats:

        await self._get_company_or_404(db, company_id)

        stats: UserQuizStatsData = (
            await self.quiz_attempt_repo.get_user_stats_for_company(
                db,
                user_id=current_user.id,
                company_id=company_id,
            )
        )

        if stats.total_questions_answered > 0:
            average = (
                stats.total_correct_answers / stats.total_questions_answered
            )
        else:
            average = 0.0

        return UserQuizStats(
            user_id=current_user.id,
            total_questions_answered=stats.total_questions_answered,
            total_correct_answers=stats.total_correct_answers,
            average_score=average,
            last_attempt_at=stats.last_attempt_at,
        )

    async def get_user_stats_global(
        self,
        db: AsyncSession,
        *,
        current_user: Any,
    ) -> UserQuizStats:

        stats: UserQuizStatsData = (
            await self.quiz_attempt_repo.get_user_stats_global(
                db,
                user_id=current_user.id,
            )
        )

        if stats.total_questions_answered > 0:
            average = (
                stats.total_correct_answers / stats.total_questions_answered
            )
        else:
            average = 0.0

        return UserQuizStats(
            user_id=current_user.id,
            total_questions_answered=stats.total_questions_answered,
            total_correct_answers=stats.total_correct_answers,
            average_score=average,
            last_attempt_at=stats.last_attempt_at,
        )
