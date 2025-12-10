from __future__ import annotations

from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import Company
from app.models.quiz import Quiz
from app.repositories.company import CompanyRepository
from app.repositories.company_member import CompanyMemberRepository
from app.repositories.quiz import QuizRepository
from app.repositories.quiz_attempt import QuizAttemptRepository
from app.repositories.notification import NotificationRepository
from app.models.notification import NotificationStatusEnum


class QuizReminderService:

    def __init__(
        self,
        company_repo: CompanyRepository | None = None,
        company_member_repo: CompanyMemberRepository | None = None,
        quiz_repo: QuizRepository | None = None,
        quiz_attempt_repo: QuizAttemptRepository | None = None,
        notification_repo: NotificationRepository | None = None,
    ) -> None:
        self.company_repo = company_repo or CompanyRepository()
        self.company_member_repo = (
            company_member_repo or CompanyMemberRepository()
        )
        self.quiz_repo = quiz_repo or QuizRepository()
        self.quiz_attempt_repo = quiz_attempt_repo or QuizAttemptRepository()
        self.notification_repo = notification_repo or NotificationRepository()

    async def _get_all_companies(
        self,
        db: AsyncSession,
    ) -> list[Company]:

        return await self.company_repo.get_all(db)

    async def _get_company_user_ids(
        self,
        db: AsyncSession,
        *,
        company: Company,
    ) -> set[int]:

        members = await self.company_member_repo.get_members_for_company(
            db,
            company_id=company.id,
        )

        user_ids: set[int] = {m.user_id for m in members}
        user_ids.add(company.owner_id)

        return user_ids

    async def _get_company_quizzes(
        self,
        db: AsyncSession,
        *,
        company: Company,
    ) -> list[Quiz]:

        return await self.quiz_repo.get_all_for_company_simple(
            db,
            company_id=company.id,
        )

    async def _get_user_last_attempts_map(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        company_id: UUID,
    ) -> dict[UUID, datetime]:

        rows = await self.quiz_attempt_repo.get_user_quiz_last_attempts(
            db,
            user_id=user_id,
            company_id=company_id,
        )

        result: dict[UUID, datetime] = {}

        for quiz_id, company_id_row, last_attempt_at in rows:
            if last_attempt_at is not None:
                result[quiz_id] = last_attempt_at

        return result

    async def _get_overdue_quizzes_for_user(
        self,
        db: AsyncSession,
        *,
        company: Company,
        user_id: int,
        now_utc: datetime,
        period_hours: int = 24,
    ) -> list[Quiz]:

        quizzes = await self._get_company_quizzes(db, company=company)
        if not quizzes:
            return []

        last_attempts_map = await self._get_user_last_attempts_map(
            db,
            user_id=user_id,
            company_id=company.id,
        )

        cutoff = now_utc - timedelta(hours=period_hours)

        overdue_quizzes: list[Quiz] = []

        for quiz in quizzes:
            last_attempt_at = last_attempts_map.get(quiz.id)

            if last_attempt_at is None or last_attempt_at < cutoff:
                overdue_quizzes.append(quiz)

        return overdue_quizzes

    async def _create_reminder_notification_for_user(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        company: Company,
        overdue_quizzes: list[Quiz],
    ) -> None:

        if not overdue_quizzes:
            return

        quiz_titles = [q.title for q in overdue_quizzes]
        quizzes_str = ", ".join(f'"{title}"' for title in quiz_titles)

        message = (
            "You have not completed the following quizzes in the last 24 hours: "
            f"{quizzes_str}. Please take them as soon as possible."
        )

        await self.notification_repo.create_one(
            db,
            user_id=user_id,
            company_id=company.id,
            quiz_id=None,
            message=message,
            status=NotificationStatusEnum.UNREAD,
        )

    async def run_daily_reminders(
        self,
        db: AsyncSession,
        *,
        period_hours: int = 24,
        now_utc: datetime | None = None,
    ) -> None:

        if now_utc is None:
            now_utc = datetime.utcnow()

        companies = await self._get_all_companies(db)
        if not companies:
            return

        for company in companies:
            user_ids = await self._get_company_user_ids(db, company=company)
            if not user_ids:
                continue

            for user_id in user_ids:
                overdue_quizzes = await self._get_overdue_quizzes_for_user(
                    db,
                    company=company,
                    user_id=user_id,
                    now_utc=now_utc,
                    period_hours=period_hours,
                )

                if not overdue_quizzes:
                    continue

                await self._create_reminder_notification_for_user(
                    db,
                    user_id=user_id,
                    company=company,
                    overdue_quizzes=overdue_quizzes,
                )
