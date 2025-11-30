from datetime import datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest
from unittest.mock import AsyncMock, ANY

from app.services.quiz import QuizService
from app.repositories.quiz_attempt import (
    QuizAttemptRepository,
    CompanyWeeklyStatsRow,
    CompanyUserQuizWeeklyRow,
    CompanyUserLastAttemptRow,
)


@pytest.mark.asyncio
async def test_get_company_weekly_stats_computes_average_and_checks_permissions():

    company_id = uuid4()
    start = datetime(2025, 11, 1)
    end = datetime(2025, 11, 30)

    quiz_attempt_repo_mock = AsyncMock(spec=QuizAttemptRepository)

    service = QuizService(
        quiz_repo=None,
        company_repo=None,
        company_member_repo=None,
        quiz_attempt_repo=quiz_attempt_repo_mock,
        quiz_redis_repo=None,
    )

    fake_company = SimpleNamespace(id=company_id)
    service._get_company_or_404 = AsyncMock(return_value=fake_company)
    service._ensure_is_company_admin = AsyncMock()

    week_start = datetime(2025, 11, 3)
    quiz_attempt_repo_mock.get_company_weekly_aggregates.return_value = [
        CompanyWeeklyStatsRow(
            week_start=week_start,
            total_questions=10,
            total_correct_answers=7,
            attempts_count=3,
        )
    ]

    current_user = SimpleNamespace(id=1)

    result = await service.get_company_weekly_stats(
        db=None,
        company_id=company_id,
        current_user=current_user,
        start=start,
        end=end,
    )

    service._get_company_or_404.assert_awaited_once_with(None, company_id)
    service._ensure_is_company_admin.assert_awaited_once_with(
        None,
        company=fake_company,
        current_user=current_user,
    )

    quiz_attempt_repo_mock.get_company_weekly_aggregates.assert_awaited_once_with(
        None,
        company_id=company_id,
        start=start,
        end=end,
    )

    assert result.company_id == company_id
    assert len(result.items) == 1

    item = result.items[0]
    assert item.week_start == week_start
    assert item.total_questions == 10
    assert item.total_correct_answers == 7
    assert item.attempts_count == 3
    assert item.average_score == pytest.approx(0.7)


@pytest.mark.asyncio
async def test_get_company_weekly_stats_handles_zero_questions():

    company_id = uuid4()

    quiz_attempt_repo_mock = AsyncMock(spec=QuizAttemptRepository)

    service = QuizService(
        quiz_repo=None,
        company_repo=None,
        company_member_repo=None,
        quiz_attempt_repo=quiz_attempt_repo_mock,
        quiz_redis_repo=None,
    )

    fake_company = SimpleNamespace(id=company_id)
    service._get_company_or_404 = AsyncMock(return_value=fake_company)
    service._ensure_is_company_admin = AsyncMock()

    week_start = datetime(2025, 11, 10)
    quiz_attempt_repo_mock.get_company_weekly_aggregates.return_value = [
        CompanyWeeklyStatsRow(
            week_start=week_start,
            total_questions=0,
            total_correct_answers=0,
            attempts_count=1,
        )
    ]

    current_user = SimpleNamespace(id=1)

    result = await service.get_company_weekly_stats(
        db=None,
        company_id=company_id,
        current_user=current_user,
        start=None,
        end=None,
    )

    assert len(result.items) == 1
    item = result.items[0]

    assert item.total_questions == 0
    assert item.total_correct_answers == 0
    assert item.average_score == 0.0


@pytest.mark.asyncio
async def test_get_company_user_quiz_weekly_stats_uses_repo_and_computes_average():

    company_id = uuid4()
    target_user_id = 42

    quiz_attempt_repo_mock = AsyncMock(spec=QuizAttemptRepository)

    service = QuizService(
        quiz_repo=None,
        company_repo=None,
        company_member_repo=None,
        quiz_attempt_repo=quiz_attempt_repo_mock,
        quiz_redis_repo=None,
    )

    fake_company = SimpleNamespace(id=company_id)
    service._get_company_or_404 = AsyncMock(return_value=fake_company)
    service._ensure_is_company_admin = AsyncMock()

    quiz_id = uuid4()
    week_start = datetime(2025, 11, 17)

    quiz_attempt_repo_mock.get_company_user_quiz_weekly_aggregates.return_value = [
        CompanyUserQuizWeeklyRow(
            quiz_id=quiz_id,
            week_start=week_start,
            total_questions=5,
            total_correct_answers=4,
            attempts_count=2,
        )
    ]

    current_user = SimpleNamespace(id=1)

    result = await service.get_company_user_quiz_weekly_stats(
        db=None,
        company_id=company_id,
        current_user=current_user,
        target_user_id=target_user_id,
        start=None,
        end=None,
    )

    service._ensure_is_company_admin.assert_awaited_once_with(
        None,
        company=fake_company,
        current_user=current_user,
    )

    quiz_attempt_repo_mock.get_company_user_quiz_weekly_aggregates.assert_awaited_once_with(
        None,
        company_id=company_id,
        user_id=target_user_id,
        start=None,
        end=None,
    )

    assert result.company_id == company_id
    assert result.user_id == target_user_id
    assert len(result.items) == 1

    item = result.items[0]
    assert item.quiz_id == quiz_id
    assert item.week_start == week_start
    assert item.total_questions == 5
    assert item.total_correct_answers == 4
    assert item.attempts_count == 2
    assert item.average_score == pytest.approx(0.8)


@pytest.mark.asyncio
async def test_get_company_users_last_attempts_maps_rows_correctly_and_checks_permissions():

    company_id = uuid4()

    quiz_attempt_repo_mock = AsyncMock(spec=QuizAttemptRepository)

    service = QuizService(
        quiz_repo=None,
        company_repo=None,
        company_member_repo=None,
        quiz_attempt_repo=quiz_attempt_repo_mock,
        quiz_redis_repo=None,
    )

    fake_company = SimpleNamespace(id=company_id)
    service._get_company_or_404 = AsyncMock(return_value=fake_company)
    service._ensure_is_company_admin = AsyncMock()

    last1 = datetime(2025, 11, 25, 12, 0, 0)
    last2 = datetime(2025, 11, 26, 15, 30, 0)

    quiz_attempt_repo_mock.get_company_users_last_attempts.return_value = [
        CompanyUserLastAttemptRow(user_id=1, last_attempt_at=last1),
        CompanyUserLastAttemptRow(user_id=2, last_attempt_at=last2),
    ]

    current_user = SimpleNamespace(id=999)

    result = await service.get_company_users_last_attempts(
        db=None,
        company_id=company_id,
        current_user=current_user,
    )

    service._ensure_is_company_admin.assert_awaited_once_with(
        None,
        company=fake_company,
        current_user=current_user,
    )

    quiz_attempt_repo_mock.get_company_users_last_attempts.assert_awaited_once_with(
        None,
        company_id=company_id,
    )

    assert result.company_id == company_id
    assert len(result.items) == 2

    u1 = next(i for i in result.items if i.user_id == 1)
    assert u1.last_attempt_at == last1

    u2 = next(i for i in result.items if i.user_id == 2)
    assert u2.last_attempt_at == last2
