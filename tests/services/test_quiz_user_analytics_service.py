from datetime import datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest
from unittest.mock import AsyncMock

from app.services.quiz import QuizService
from app.repositories.quiz_attempt import (
    QuizAttemptRepository,
    UserQuizAggregateRow,
    UserQuizLastAttemptRow,
    UserQuizStatsData,
)


@pytest.mark.asyncio
async def test_get_user_overall_rating_delegates_to_get_user_stats_global():

    quiz_attempt_repo_mock = AsyncMock(spec=QuizAttemptRepository)

    service = QuizService(
        quiz_repo=None,
        company_repo=None,
        company_member_repo=None,
        quiz_attempt_repo=quiz_attempt_repo_mock,
        quiz_redis_repo=None,
    )

    fake_stats = SimpleNamespace(
        user_id=123,
        total_questions_answered=10,
        total_correct_answers=8,
        average_score=0.8,
        last_attempt_at=datetime(2025, 11, 27, 12, 0, 0),
    )
    service.get_user_stats_global = AsyncMock(return_value=fake_stats)

    current_user = SimpleNamespace(id=123)

    result = await service.get_user_overall_rating(
        db=None,
        current_user=current_user,
    )

    service.get_user_stats_global.assert_awaited_once_with(
        None,
        current_user=current_user,
    )
    assert result is fake_stats


@pytest.mark.asyncio
async def test_get_user_quiz_average_scores_uses_repo_and_computes_average():

    quiz_attempt_repo_mock = AsyncMock(spec=QuizAttemptRepository)

    service = QuizService(
        quiz_repo=None,
        company_repo=None,
        company_member_repo=None,
        quiz_attempt_repo=quiz_attempt_repo_mock,
        quiz_redis_repo=None,
    )

    current_user = SimpleNamespace(id=123)
    start = datetime(2025, 11, 1)
    end = datetime(2025, 11, 30)
    company_id = uuid4()

    quiz_id = uuid4()
    quiz_attempt_repo_mock.get_user_quiz_aggregates_in_range.return_value = [
        UserQuizAggregateRow(
            quiz_id=quiz_id,
            company_id=company_id,
            total_questions=10,
            total_correct_answers=7,
            attempts_count=3,
        )
    ]

    result = await service.get_user_quiz_average_scores(
        db=None,
        current_user=current_user,
        start=start,
        end=end,
        company_id=company_id,
    )

    quiz_attempt_repo_mock.get_user_quiz_aggregates_in_range.assert_awaited_once_with(
        None,
        user_id=current_user.id,
        start=start,
        end=end,
        company_id=company_id,
    )

    assert result.user_id == current_user.id
    assert len(result.items) == 1

    item = result.items[0]
    assert item.quiz_id == quiz_id
    assert item.company_id == company_id
    assert item.total_questions == 10
    assert item.total_correct_answers == 7
    assert item.attempts_count == 3
    assert item.period_from == start
    assert item.period_to == end
    assert item.average_score == pytest.approx(0.7)


@pytest.mark.asyncio
async def test_get_user_quiz_average_scores_handles_zero_questions():

    quiz_attempt_repo_mock = AsyncMock(spec=QuizAttemptRepository)

    service = QuizService(
        quiz_repo=None,
        company_repo=None,
        company_member_repo=None,
        quiz_attempt_repo=quiz_attempt_repo_mock,
        quiz_redis_repo=None,
    )

    current_user = SimpleNamespace(id=123)

    quiz_id = uuid4()
    company_id = uuid4()
    quiz_attempt_repo_mock.get_user_quiz_aggregates_in_range.return_value = [
        UserQuizAggregateRow(
            quiz_id=quiz_id,
            company_id=company_id,
            total_questions=0,
            total_correct_answers=0,
            attempts_count=1,
        )
    ]

    result = await service.get_user_quiz_average_scores(
        db=None,
        current_user=current_user,
        start=None,
        end=None,
        company_id=None,
    )

    assert len(result.items) == 1
    item = result.items[0]
    assert item.total_questions == 0
    assert item.total_correct_answers == 0
    assert item.average_score == 0.0


@pytest.mark.asyncio
async def test_get_user_quiz_last_attempts_maps_rows_correctly():

    quiz_attempt_repo_mock = AsyncMock(spec=QuizAttemptRepository)

    service = QuizService(
        quiz_repo=None,
        company_repo=None,
        company_member_repo=None,
        quiz_attempt_repo=quiz_attempt_repo_mock,
        quiz_redis_repo=None,
    )

    current_user = SimpleNamespace(id=123)
    company_id = uuid4()

    quiz_id_1 = uuid4()
    quiz_id_2 = uuid4()
    last1 = datetime(2025, 11, 25, 10, 0, 0)
    last2 = datetime(2025, 11, 26, 11, 30, 0)

    quiz_attempt_repo_mock.get_user_quiz_last_attempts.return_value = [
        UserQuizLastAttemptRow(
            quiz_id=quiz_id_1,
            company_id=company_id,
            last_attempt_at=last1,
        ),
        UserQuizLastAttemptRow(
            quiz_id=quiz_id_2,
            company_id=company_id,
            last_attempt_at=last2,
        ),
    ]

    result = await service.get_user_quiz_last_attempts(
        db=None,
        current_user=current_user,
        company_id=company_id,
    )

    quiz_attempt_repo_mock.get_user_quiz_last_attempts.assert_awaited_once_with(
        None,
        user_id=current_user.id,
        company_id=company_id,
    )

    assert result.user_id == current_user.id
    assert len(result.items) == 2

    q1 = next(i for i in result.items if i.quiz_id == quiz_id_1)
    assert q1.company_id == company_id
    assert q1.last_attempt_at == last1

    q2 = next(i for i in result.items if i.quiz_id == quiz_id_2)
    assert q2.company_id == company_id
    assert q2.last_attempt_at == last2
