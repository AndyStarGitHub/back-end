from types import SimpleNamespace
from uuid import uuid4

import pytest
from unittest.mock import AsyncMock, Mock

from app.services.quiz import QuizService
from app.repositories.quiz_attempt import QuizAttemptRepository
from app.repositories.quiz_redis import QuizRedisRepository
from app.schemas.quiz import QuizSubmit, QuizAnswerSubmit


@pytest.mark.asyncio
async def test_submit_quiz_calls_redis_save_attempt():

    company_id = uuid4()
    quiz_id = uuid4()

    quiz_repo_mock = Mock()
    company_repo_mock = Mock()
    company_member_repo_mock = Mock()
    quiz_attempt_repo_mock = AsyncMock(spec=QuizAttemptRepository)
    quiz_redis_repo_mock = AsyncMock(spec=QuizRedisRepository)

    service = QuizService(
        quiz_repo=quiz_repo_mock,
        company_repo=company_repo_mock,
        company_member_repo=company_member_repo_mock,
        quiz_attempt_repo=quiz_attempt_repo_mock,
        quiz_redis_repo=quiz_redis_repo_mock,
    )

    fake_company = SimpleNamespace(id=company_id)
    fake_quiz = SimpleNamespace(
        id=quiz_id,
        company_id=company_id,
    )

    current_user = SimpleNamespace(id=123)

    fake_attempt = SimpleNamespace(
        id=uuid4(),
        user_id=current_user.id,
        company_id=company_id,
        quiz_id=quiz_id,
        total_questions=3,
        correct_answers=2,
        created_at=None,
        answers=[],
    )

    service._get_company_or_404 = AsyncMock(return_value=fake_company)
    service._get_quiz_or_404 = AsyncMock(return_value=fake_quiz)

    service._prepare_attempt_data = Mock(
        return_value=(3, 2, ["dummy_answers"]),
    )

    quiz_attempt_repo_mock.create_attempt_with_answers.return_value = fake_attempt

    submit_data = QuizSubmit(
        answers=[
            QuizAnswerSubmit(
                question_id=uuid4(),
                selected_option_ids=[uuid4()],
            )
        ]
    )

    result = await service.submit_quiz(
        db=None,
        company_id=company_id,
        quiz_id=quiz_id,
        current_user=current_user,
        data=submit_data,
    )

    quiz_redis_repo_mock.save_attempt.assert_awaited_once_with(fake_attempt)

    assert result.id == fake_attempt.id
    assert result.user_id == current_user.id
    assert result.company_id == company_id
    assert result.quiz_id == quiz_id
    assert result.total_questions == 3
    assert result.correct_answers == 2
