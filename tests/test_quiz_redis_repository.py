import json
from uuid import uuid4

import pytest
from unittest.mock import AsyncMock

from app.repositories.quiz_redis import QuizRedisRepository
from app.models.quiz_attempt import (
    QuizAttempt,
    QuizAttemptAnswer,
    QuizAttemptAnswerOption,
)


@pytest.mark.asyncio
async def test_quiz_redis_repository_save_attempt_stores_correct_payload_and_ttl():

    redis_mock = AsyncMock()

    repo = QuizRedisRepository(redis_mock, ttl_seconds=123)

    attempt_id = uuid4()
    company_id = uuid4()
    quiz_id = uuid4()
    question_id = uuid4()
    option_id_1 = uuid4()
    option_id_2 = uuid4()

    attempt = QuizAttempt(
        id=attempt_id,
        user_id=1,
        company_id=company_id,
        quiz_id=quiz_id,
        total_questions=1,
        correct_answers=1,
    )

    answer = QuizAttemptAnswer(
        question_id=question_id,
        is_correct=True,
    )

    selected_opt_1 = QuizAttemptAnswerOption(option_id=option_id_1)
    selected_opt_2 = QuizAttemptAnswerOption(option_id=option_id_2)

    answer.selected_options.extend([selected_opt_1, selected_opt_2])
    attempt.answers.append(answer)

    await repo.save_attempt(attempt)

    redis_mock.set.assert_awaited_once()
    called_args, called_kwargs = redis_mock.set.await_args

    key = called_args[0]
    payload_json = called_args[1]
    ttl = called_kwargs.get("ex")

    assert key == f"quiz:attempt:{attempt_id}"
    assert ttl == 123

    payload = json.loads(payload_json)

    assert payload["attempt_id"] == str(attempt_id)
    assert payload["user_id"] == 1
    assert payload["company_id"] == str(company_id)
    assert payload["quiz_id"] == str(quiz_id)
    assert payload["total_questions"] == 1
    assert payload["correct_answers"] == 1

    assert len(payload["answers"]) == 1
    ans_payload = payload["answers"][0]
    assert ans_payload["question_id"] == str(question_id)
    assert ans_payload["is_correct"] is True

    assert set(ans_payload["selected_option_ids"]) == {
        str(option_id_1),
        str(option_id_2),
    }


@pytest.mark.asyncio
async def test_quiz_redis_repository_get_attempt_parses_json():

    redis_mock = AsyncMock()
    repo = QuizRedisRepository(redis_mock)

    attempt_id = uuid4()
    fake_data = {"attempt_id": str(attempt_id), "user_id": 42}
    redis_mock.get.return_value = json.dumps(fake_data)

    result = await repo.get_attempt(attempt_id)

    redis_mock.get.assert_awaited_once_with(f"quiz:attempt:{attempt_id}")
    assert result == fake_data
