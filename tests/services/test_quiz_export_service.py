import csv
from types import SimpleNamespace
from uuid import uuid4

import pytest
from unittest.mock import AsyncMock, ANY

from app.services.quiz import QuizService
from app.repositories.quiz_attempt import QuizAttemptRepository
from app.repositories.quiz_redis import QuizRedisRepository


def test_build_csv_export_produces_rows_per_answer():

    attempt_id_1 = str(uuid4())
    attempt_id_2 = str(uuid4())
    company_id = str(uuid4())
    quiz_id = str(uuid4())

    payloads = [
        {
            "attempt_id": attempt_id_1,
            "user_id": 1,
            "company_id": company_id,
            "quiz_id": quiz_id,
            "total_questions": 2,
            "correct_answers": 1,
            "created_at": "2025-11-27T12:00:00Z",
            "answers": [
                {
                    "question_id": str(uuid4()),
                    "selected_option_ids": ["opt1", "opt2"],
                    "is_correct": True,
                },
                {
                    "question_id": str(uuid4()),
                    "selected_option_ids": ["opt3"],
                    "is_correct": False,
                },
            ],
        },
        {
            "attempt_id": attempt_id_2,
            "user_id": 2,
            "company_id": company_id,
            "quiz_id": quiz_id,
            "total_questions": 1,
            "correct_answers": 1,
            "created_at": "2025-11-27T13:00:00Z",
            "answers": [
                {
                    "question_id": str(uuid4()),
                    "selected_option_ids": ["opt4"],
                    "is_correct": True,
                }
            ],
        },
    ]

    service = QuizService(
        quiz_repo=None,
        company_repo=None,
        company_member_repo=None,
        quiz_attempt_repo=None,
        quiz_redis_repo=None,
    )

    csv_str = service._build_csv_export(payloads)

    lines = csv_str.strip().splitlines()

    assert len(lines) == 1 + 3

    reader = csv.reader(lines)
    header = next(reader)

    assert header == [
        "attempt_id",
        "attempt_created_at",
        "user_id",
        "company_id",
        "quiz_id",
        "question_id",
        "is_correct",
        "selected_option_ids",
    ]

    rows = list(reader)

    for row in rows:
        assert len(row) == 8

    attempt_ids_in_csv = {row[0] for row in rows}
    assert attempt_ids_in_csv == {attempt_id_1, attempt_id_2}


@pytest.mark.asyncio
async def test_export_my_attempts_for_company_json():

    company_id = uuid4()

    quiz_attempt_repo_mock = AsyncMock(spec=QuizAttemptRepository)
    quiz_redis_repo_mock = AsyncMock(spec=QuizRedisRepository)

    service = QuizService(
        quiz_repo=None,
        company_repo=None,
        company_member_repo=None,
        quiz_attempt_repo=quiz_attempt_repo_mock,
        quiz_redis_repo=quiz_redis_repo_mock,
    )

    fake_company = SimpleNamespace(id=company_id)
    service._get_company_or_404 = AsyncMock(return_value=fake_company)

    attempt_id = uuid4()
    fake_attempt = SimpleNamespace(id=attempt_id)

    quiz_attempt_repo_mock.get_attempts_for_company_and_user.return_value = [fake_attempt]

    fake_payload = {
        "attempt_id": str(attempt_id),
        "user_id": 123,
        "company_id": str(company_id),
        "quiz_id": str(uuid4()),
        "total_questions": 2,
        "correct_answers": 1,
        "created_at": "2025-11-27T12:00:00Z",
        "answers": [],
    }
    quiz_redis_repo_mock.get_attempt.return_value = fake_payload

    current_user = SimpleNamespace(id=123)

    result = await service.export_my_attempts_for_company(
        db=None,
        company_id=company_id,
        current_user=current_user,
        format="json",
        quiz_id=None,
    )

    quiz_attempt_repo_mock.get_attempts_for_company_and_user.assert_awaited_once()

    quiz_attempt_repo_mock.get_attempts_for_company_and_user.assert_awaited_with(
        None,
        company_id=company_id,
        user_id=current_user.id,
        since=ANY,
        quiz_id=None,
    )

    quiz_redis_repo_mock.get_attempt.assert_awaited_once_with(attempt_id)

    assert result["company_id"] == str(company_id)
    assert result["filter"]["user_id"] == current_user.id
    assert result["filter"]["quiz_id"] is None

    assert len(result["attempts"]) == 1
    assert result["attempts"][0]["attempt_id"] == str(attempt_id)


@pytest.mark.asyncio
async def test_export_company_attempts_csv_for_admin():

    company_id = uuid4()
    quiz_id = uuid4()

    quiz_attempt_repo_mock = AsyncMock(spec=QuizAttemptRepository)
    quiz_redis_repo_mock = AsyncMock(spec=QuizRedisRepository)

    service = QuizService(
        quiz_repo=None,
        company_repo=None,
        company_member_repo=None,
        quiz_attempt_repo=quiz_attempt_repo_mock,
        quiz_redis_repo=quiz_redis_repo_mock,
    )

    fake_company = SimpleNamespace(id=company_id)
    service._get_company_or_404 = AsyncMock(return_value=fake_company)

    service._ensure_is_company_admin = AsyncMock()

    attempt_id = uuid4()
    fake_attempt = SimpleNamespace(id=attempt_id)

    quiz_attempt_repo_mock.get_attempts_for_company.return_value = [fake_attempt]

    fake_payload = {
        "attempt_id": str(attempt_id),
        "user_id": 999,
        "company_id": str(company_id),
        "quiz_id": str(quiz_id),
        "total_questions": 1,
        "correct_answers": 1,
        "created_at": "2025-11-27T15:00:00Z",
        "answers": [
            {
                "question_id": str(uuid4()),
                "selected_option_ids": ["opt1"],
                "is_correct": True,
            }
        ],
    }
    quiz_redis_repo_mock.get_attempt.return_value = fake_payload

    current_user = SimpleNamespace(id=1)

    csv_result = await service.export_company_attempts(
        db=None,
        company_id=company_id,
        current_user=current_user,
        format="csv",
        quiz_id=quiz_id,
    )

    service._ensure_is_company_admin.assert_awaited_once_with(
        None,
        company=fake_company,
        current_user=current_user,
    )

    quiz_attempt_repo_mock.get_attempts_for_company.assert_awaited_once()
    quiz_attempt_repo_mock.get_attempts_for_company.assert_awaited_with(
        None,
        company_id=company_id,
        since=ANY,
        quiz_id=quiz_id,
    )

    assert isinstance(csv_result, str)
    lines = csv_result.strip().splitlines()

    assert len(lines) == 2

    reader = csv.reader(lines)
    header = next(reader)
    row = next(reader)

    assert header[0] == "attempt_id"
    assert row[0] == str(attempt_id)
