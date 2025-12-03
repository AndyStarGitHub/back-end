from __future__ import annotations

from typing import Any, Literal
from uuid import UUID
from datetime import datetime, timedelta

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

from app.schemas.quiz_analytics import (
    UserQuizAverageList,
    UserQuizAverageInRange,
    UserQuizLastAttemptList,
    UserQuizLastAttempt,
    CompanyWeeklyStats,
    CompanyWeeklyStatsItem,
    CompanyUserQuizWeeklyStats,
    CompanyUserQuizWeeklyItem,
    CompanyUsersLastAttemptList,
    CompanyUserLastAttempt,
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

    async def _get_attempt_payloads_from_redis(
        self,
        attempts: list["QuizAttempt"],
    ) -> list[dict]:

        if self.quiz_redis_repo is None:
            return []

        payloads: list[dict] = []

        for attempt in attempts:
            data = await self.quiz_redis_repo.get_attempt(attempt.id)
            if data is not None:
                payloads.append(data)

        return payloads

    def _build_csv_export(
        self,
        attempt_payloads: list[dict],
    ) -> str:

        import csv
        import io

        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow(
            [
                "attempt_id",
                "attempt_created_at",
                "user_id",
                "company_id",
                "quiz_id",
                "question_id",
                "is_correct",
                "selected_option_ids",
            ]
        )

        for payload in attempt_payloads:
            attempt_id = payload.get("attempt_id")
            created_at = payload.get("created_at")
            user_id = payload.get("user_id")
            company_id = payload.get("company_id")
            quiz_id = payload.get("quiz_id")

            answers = payload.get("answers") or []
            for ans in answers:
                question_id = ans.get("question_id")
                is_correct = ans.get("is_correct")
                selected_option_ids = ans.get("selected_option_ids") or []

                selected_joined = "|".join(selected_option_ids)

                writer.writerow(
                    [
                        attempt_id,
                        created_at,
                        user_id,
                        company_id,
                        quiz_id,
                        question_id,
                        is_correct,
                        selected_joined,
                    ]
                )

        return output.getvalue()

    async def _export_attempts(
        self,
        attempts: list["QuizAttempt"],
        *,
        format: Literal["json", "csv"],
        company_id: UUID,
        user_id: int | None = None,
        quiz_id: UUID | None = None,
    ):

        payloads = await self._get_attempt_payloads_from_redis(attempts)

        if format == "json":
            return {
                "company_id": str(company_id),
                "filter": {
                    "user_id": user_id,
                    "quiz_id": str(quiz_id) if quiz_id is not None else None,
                },
                "attempts": payloads,
            }

        if format == "csv":
            return self._build_csv_export(payloads)

        raise ValueError("Unsupported export format. Use 'json' or 'csv'.")

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

        total_q, total_correct, last_attempt_at = (
            await self.quiz_attempt_repo.get_user_stats_for_company(
                db,
                user_id=current_user.id,
                company_id=company_id,
            )
        )

        total_questions_answered = int(total_q or 0)
        total_correct_answers = int(total_correct or 0)

        if total_questions_answered > 0:
            average = total_correct_answers / total_questions_answered
        else:
            average = 0.0

        return UserQuizStats(
            user_id=current_user.id,
            total_questions_answered=total_questions_answered,
            total_correct_answers=total_correct_answers,
            average_score=average,
            last_attempt_at=last_attempt_at,
        )

    async def get_user_stats_global(
        self,
        db: AsyncSession,
        *,
        current_user: Any,
    ) -> UserQuizStats:

        total_q, total_correct, last_attempt_at = (
            await self.quiz_attempt_repo.get_user_stats_global(
                db,
                user_id=current_user.id,
            )
        )

        total_questions_answered = int(total_q or 0)
        total_correct_answers = int(total_correct or 0)

        if total_questions_answered > 0:
            average = total_correct_answers / total_questions_answered
        else:
            average = 0.0

        return UserQuizStats(
            user_id=current_user.id,
            total_questions_answered=total_questions_answered,
            total_correct_answers=total_correct_answers,
            average_score=average,
            last_attempt_at=last_attempt_at,
        )

    async def get_user_overall_rating(
        self,
        db: AsyncSession,
        *,
        current_user: Any,
    ) -> UserQuizStats:

        return await self.get_user_stats_global(db, current_user=current_user)

    async def export_my_attempts_for_company(
        self,
        db: AsyncSession,
        *,
        company_id: UUID,
        current_user: Any,
        format: Literal["json", "csv"] = "json",
        quiz_id: UUID | None = None,
    ):

        company = await self._get_company_or_404(db, company_id)

        since = datetime.utcnow() - timedelta(hours=48)

        attempts_seq = await self.quiz_attempt_repo.get_attempts_for_company_and_user(
            db,
            company_id=company.id,
            user_id=current_user.id,
            since=since,
            quiz_id=quiz_id,
        )

        attempts = list(attempts_seq)

        return await self._export_attempts(
            attempts,
            format=format,
            company_id=company.id,
            user_id=current_user.id,
            quiz_id=quiz_id,
        )

    async def export_user_attempts_for_company(
        self,
        db: AsyncSession,
        *,
        company_id: UUID,
        current_user: Any,
        target_user_id: int,
        format: Literal["json", "csv"] = "json",
        quiz_id: UUID | None = None,
    ):

        company = await self._get_company_or_404(db, company_id)

        await self._ensure_is_company_admin(
            db,
            company=company,
            current_user=current_user,
        )

        since = datetime.utcnow() - timedelta(hours=48)

        attempts_seq = await self.quiz_attempt_repo.get_attempts_for_company_and_user(
            db,
            company_id=company.id,
            user_id=target_user_id,
            since=since,
            quiz_id=quiz_id,
        )

        attempts = list(attempts_seq)

        return await self._export_attempts(
            attempts,
            format=format,
            company_id=company.id,
            user_id=target_user_id,
            quiz_id=quiz_id,
        )

    async def export_company_attempts(
        self,
        db: AsyncSession,
        *,
        company_id: UUID,
        current_user: Any,
        format: Literal["json", "csv"] = "json",
        quiz_id: UUID | None = None,
    ):

        company = await self._get_company_or_404(db, company_id)

        await self._ensure_is_company_admin(
            db,
            company=company,
            current_user=current_user,
        )

        since = datetime.utcnow() - timedelta(hours=48)

        attempts_seq = await self.quiz_attempt_repo.get_attempts_for_company(
            db,
            company_id=company.id,
            since=since,
            quiz_id=quiz_id,
        )

        attempts = list(attempts_seq)

        return await self._export_attempts(
            attempts,
            format=format,
            company_id=company.id,
            user_id=None,
            quiz_id=quiz_id,
        )

    async def get_user_quiz_average_scores(
        self,
        db: AsyncSession,
        *,
        current_user: Any,
        start: datetime | None = None,
        end: datetime | None = None,
        company_id: UUID | None = None,
    ) -> UserQuizAverageList:

        user_id = current_user.id

        rows = await self.quiz_attempt_repo.get_user_quiz_aggregates_in_range(
            db,
            user_id=user_id,
            start=start,
            end=end,
            company_id=company_id,
        )

        items: list[UserQuizAverageInRange] = []

        for quiz_id, company_id_row, total_questions, total_correct, attempts_count in rows:
            if total_questions > 0:
                average = total_correct / total_questions
            else:
                average = 0.0

            items.append(
                UserQuizAverageInRange(
                    quiz_id=quiz_id,
                    company_id=company_id_row,
                    average_score=average,
                    total_questions=total_questions,
                    total_correct_answers=total_correct,
                    attempts_count=attempts_count,
                    period_from=start,
                    period_to=end,
                )
            )

        return UserQuizAverageList(
            user_id=user_id,
            items=items,
        )

    async def get_user_quiz_last_attempts(
        self,
        db: AsyncSession,
        *,
        current_user: Any,
        company_id: UUID | None = None,
    ) -> UserQuizLastAttemptList:

        user_id = current_user.id

        rows = await self.quiz_attempt_repo.get_user_quiz_last_attempts(
            db,
            user_id=user_id,
            company_id=company_id,
        )

        items: list[UserQuizLastAttempt] = [
            UserQuizLastAttempt(
                quiz_id=quiz_id,
                company_id=company_id_row,
                last_attempt_at=last_attempt_at,
            )
            for (quiz_id, company_id_row, last_attempt_at) in rows
        ]

        return UserQuizLastAttemptList(
            user_id=user_id,
            items=items,
        )

    async def get_company_weekly_stats(
        self,
        db: AsyncSession,
        *,
        company_id: UUID,
        current_user: Any,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> CompanyWeeklyStats:

        company = await self._get_company_or_404(db, company_id)

        await self._ensure_is_company_admin(
            db,
            company=company,
            current_user=current_user,
        )

        rows = await self.quiz_attempt_repo.get_company_weekly_aggregates(
            db,
            company_id=company.id,
            start=start,
            end=end,
        )

        items: list[CompanyWeeklyStatsItem] = []

        for week_start, total_questions, total_correct, attempts_count in rows:
            if total_questions > 0:
                average = total_correct / total_questions
            else:
                average = 0.0

            items.append(
                CompanyWeeklyStatsItem(
                    week_start=week_start,
                    average_score=average,
                    total_questions=total_questions,
                    total_correct_answers=total_correct,
                    attempts_count=attempts_count,
                )
            )

        return CompanyWeeklyStats(
            company_id=company.id,
            items=items,
        )

    async def get_company_user_quiz_weekly_stats(
        self,
        db: AsyncSession,
        *,
        company_id: UUID,
        current_user: Any,
        target_user_id: int,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> CompanyUserQuizWeeklyStats:

        company = await self._get_company_or_404(db, company_id)

        await self._ensure_is_company_admin(
            db,
            company=company,
            current_user=current_user,
        )

        rows = await self.quiz_attempt_repo.get_company_user_quiz_weekly_aggregates(
            db,
            company_id=company.id,
            user_id=target_user_id,
            start=start,
            end=end,
        )

        items: list[CompanyUserQuizWeeklyItem] = []

        for quiz_id, week_start, total_questions, total_correct, attempts_count in rows:
            if total_questions > 0:
                average = total_correct / total_questions
            else:
                average = 0.0

            items.append(
                CompanyUserQuizWeeklyItem(
                    quiz_id=quiz_id,
                    week_start=week_start,
                    average_score=average,
                    total_questions=total_questions,
                    total_correct_answers=total_correct,
                    attempts_count=attempts_count,
                )
            )

        return CompanyUserQuizWeeklyStats(
            company_id=company.id,
            user_id=target_user_id,
            items=items,
        )

    async def get_company_users_last_attempts(
        self,
        db: AsyncSession,
        *,
        company_id: UUID,
        current_user: Any,
    ) -> CompanyUsersLastAttemptList:

        company = await self._get_company_or_404(db, company_id)

        await self._ensure_is_company_admin(
            db,
            company=company,
            current_user=current_user,
        )

        rows = await self.quiz_attempt_repo.get_company_users_last_attempts(
            db,
            company_id=company.id,
        )

        items: list[CompanyUserLastAttempt] = [
            CompanyUserLastAttempt(
                user_id=user_id,
                last_attempt_at=last_attempt_at,
            )
            for (user_id, last_attempt_at) in rows
        ]

        return CompanyUsersLastAttemptList(
            company_id=company.id,
            items=items,
        )
