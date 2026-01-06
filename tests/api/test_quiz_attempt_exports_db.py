from __future__ import annotations

import json
from datetime import datetime, timezone, date

import pytest

from app.models.quiz import Quiz, QuizQuestion, QuizAnswerOption
from app.models.quiz_attempt import (
    QuizAttempt,
    QuizAttemptAnswer,
    QuizAttemptAnswerOption
)
from app.models.company_member import CompanyMemberRoleEnum


def _utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


async def _create_quiz_with_question_and_options(db_session, *, company_id):
    quiz = Quiz(
        company_id=company_id,
        title="Export Quiz",
        description="",
        frequency="monthly",
    )
    q1 = QuizQuestion(title="What is 2+2?")
    opt1 = QuizAnswerOption(text="4", is_correct=True)
    opt2 = QuizAnswerOption(text="5", is_correct=False)
    q1.options.append(opt1)
    q1.options.append(opt2)
    quiz.questions.append(q1)

    db_session.add(quiz)
    await db_session.commit()
    await db_session.refresh(quiz)

    await db_session.refresh(q1)
    await db_session.refresh(opt1)
    await db_session.refresh(opt2)

    return quiz, q1, opt1, opt2


async def _create_attempt_with_answer(
    db_session,
    *,
    user_id: int,
    company_id,
    quiz_id,
    question_id,
    selected_option_ids: list,
    is_correct: bool,
    total_questions: int = 1,
    correct_answers: int = 1,
    created_at: datetime | None = None,
):
    attempt = QuizAttempt(
        user_id=user_id,
        company_id=company_id,
        quiz_id=quiz_id,
        total_questions=total_questions,
        correct_answers=correct_answers,
    )
    if created_at is not None:
        attempt.created_at = created_at

    ans = QuizAttemptAnswer(
        question_id=question_id,
        is_correct=is_correct,
    )

    for oid in selected_option_ids:
        ans.selected_options.append(QuizAttemptAnswerOption(option_id=oid))

    attempt.answers.append(ans)

    db_session.add(attempt)
    await db_session.commit()
    await db_session.refresh(attempt)
    return attempt


def _assert_file_headers(resp, *, ext: str, must_contain: str):
    assert resp.status_code == 200
    cd = (resp.headers.get("content-disposition")
          or resp.headers.get("Content-Disposition"))
    assert cd is not None
    assert "attachment" in cd
    assert cd.endswith(f'.{ext}"') or f".{ext}" in cd
    assert must_contain in cd
    return cd


@pytest.mark.anyio
async def test_me_export_db_requires_auth(client, override_current_user):
    override_current_user(None)

    resp = await client.get(
        "/api/v1/me/quiz-attempts/export/db?company_id=00000000-0000-0000-0000-000000000000"
    )
    assert resp.status_code == 401


@pytest.mark.anyio
async def test_me_export_db_json_includes_question_and_option_texts(
    client,
    db_session,
    override_current_user,
    user_factory,
    company_factory,
):
    user = await user_factory(email="me@test.com")
    override_current_user(user)

    company = await company_factory(owner=user, name="C-Export-Me")
    quiz, question, opt1, opt2 = await _create_quiz_with_question_and_options(
        db_session,
        company_id=company.id,
    )

    await _create_attempt_with_answer(
        db_session,
        user_id=user.id,
        company_id=company.id,
        quiz_id=quiz.id,
        question_id=question.id,
        selected_option_ids=[opt1.id],
        is_correct=True,
        created_at=_utc(datetime(2025, 12, 29, 10, 0, 0)),
        total_questions=1,
        correct_answers=1,
    )

    resp = await client.get(
        f"/api/v1/me/quiz-attempts/export/db?company_id={company.id}&format=json"
    )

    _assert_file_headers(resp, ext="json", must_contain=str(company.id))
    assert resp.headers["content-type"].startswith("application/json")

    payload = resp.json()
    assert payload["company_id"] == str(company.id)
    assert payload["attempts"]

    att = payload["attempts"][0]
    assert att["user_id"] == user.id
    assert att["quiz_id"] == str(quiz.id)

    ans = att["answers"][0]
    assert ans["question_id"] == str(question.id)
    assert ans["question_title"] == "What is 2+2?"
    assert ans["selected_options"][0]["option_text"] == "4"


@pytest.mark.anyio
async def test_me_export_db_csv_has_text_columns(
    client,
    db_session,
    override_current_user,
    user_factory,
    company_factory,
):
    user = await user_factory(email="me2@test.com")
    override_current_user(user)

    company = await company_factory(owner=user, name="C-Export-Me-CSV")
    quiz, question, opt1, opt2 = await _create_quiz_with_question_and_options(
        db_session,
        company_id=company.id,
    )

    await _create_attempt_with_answer(
        db_session,
        user_id=user.id,
        company_id=company.id,
        quiz_id=quiz.id,
        question_id=question.id,
        selected_option_ids=[opt2.id],
        is_correct=False,
        total_questions=1,
        correct_answers=0,
    )

    resp = await client.get(
        f"/api/v1/me/quiz-attempts/export/db?company_id={company.id}&format=csv"
    )

    _assert_file_headers(resp, ext="csv", must_contain=str(company.id))
    assert resp.headers["content-type"].startswith("text/csv")

    text = resp.text
    assert "question_title" in text
    assert "selected_option_texts" in text
    assert "What is 2+2?" in text
    assert "5" in text


@pytest.mark.anyio
async def test_company_export_db_forbidden_for_member(
    client,
    db_session,
    override_current_user,
    user_factory,
    company_factory,
    company_member_factory,
):
    owner = await user_factory(email="owner@test.com")
    member = await user_factory(email="member@test.com")

    company = await company_factory(owner=owner, name="C-Export-Company")
    await company_member_factory(
        company=company,
        user=member,
        role=CompanyMemberRoleEnum.MEMBER
    )

    override_current_user(member)

    resp = await client.get(
        f"/api/v1/companies/{company.id}/quiz-attempts/export/db?format=json"
    )
    assert resp.status_code == 403


@pytest.mark.anyio
async def test_company_export_db_json_includes_multiple_users(
    client,
    db_session,
    override_current_user,
    user_factory,
    company_factory,
):
    owner = await user_factory(email="owner2@test.com")
    other = await user_factory(email="other@test.com")

    company = await company_factory(owner=owner, name="C-Export-Company-2")
    override_current_user(owner)

    quiz, question, opt1, opt2 = await _create_quiz_with_question_and_options(
        db_session,
        company_id=company.id,
    )

    await _create_attempt_with_answer(
        db_session,
        user_id=owner.id,
        company_id=company.id,
        quiz_id=quiz.id,
        question_id=question.id,
        selected_option_ids=[opt1.id],
        is_correct=True,
    )

    await _create_attempt_with_answer(
        db_session,
        user_id=other.id,
        company_id=company.id,
        quiz_id=quiz.id,
        question_id=question.id,
        selected_option_ids=[opt2.id],
        is_correct=False,
    )

    resp = await client.get(
        f"/api/v1/companies/{company.id}/quiz-attempts/export/db?format=json"
    )

    _assert_file_headers(resp, ext="json", must_contain=str(company.id))
    payload = resp.json()
    user_ids = {a["user_id"] for a in payload["attempts"]}
    assert owner.id in user_ids
    assert other.id in user_ids


@pytest.mark.anyio
async def test_company_export_db_csv_respects_quiz_filter(
    client,
    db_session,
    override_current_user,
    user_factory,
    company_factory,
):
    owner = await user_factory(email="owner3@test.com")
    override_current_user(owner)

    company = await company_factory(owner=owner, name="C-Export-Company-CSV")

    quiz1, q1, opt1a, opt1b = await _create_quiz_with_question_and_options(
        db_session,
        company_id=company.id,
    )

    quiz2 = Quiz(
        company_id=company.id,
        title="Other Quiz",
        description="",
        frequency="monthly",
    )
    db_session.add(quiz2)
    await db_session.commit()
    await db_session.refresh(quiz2)

    await _create_attempt_with_answer(
        db_session,
        user_id=owner.id,
        company_id=company.id,
        quiz_id=quiz1.id,
        question_id=q1.id,
        selected_option_ids=[opt1a.id],
        is_correct=True,
    )
    await _create_attempt_with_answer(
        db_session,
        user_id=owner.id,
        company_id=company.id,
        quiz_id=quiz2.id,
        question_id=q1.id,
        selected_option_ids=[opt1a.id],
        is_correct=True,
    )

    resp = await client.get(
        f"/api/v1/companies/{company.id}/quiz-attempts/export/db?format=csv&quiz_id={quiz1.id}"
    )

    _assert_file_headers(resp, ext="csv", must_contain=str(company.id))
    cd = resp.headers.get("content-disposition", "")
    assert f"_quiz_{quiz1.id}" in cd

    text = resp.text

    assert str(quiz1.id) in text
    assert str(quiz2.id) not in text


@pytest.mark.anyio
async def test_company_user_export_db_forbidden_for_member(
    client,
    override_current_user,
    user_factory,
    company_factory,
    company_member_factory,
):
    owner = await user_factory(email="owner4@test.com")
    member = await user_factory(email="member2@test.com")
    target = await user_factory(email="target@test.com")

    company = await company_factory(owner=owner, name="C-Export-User")
    await company_member_factory(
        company=company,
        user=member,
        role=CompanyMemberRoleEnum.MEMBER
    )

    override_current_user(member)

    resp = await client.get(
        f"/api/v1/companies/{company.id}/users/{target.id}/quiz-attempts/export/db?format=json"
    )
    assert resp.status_code == 403


@pytest.mark.anyio
async def test_company_user_export_db_json_only_target_user(
    client,
    db_session,
    override_current_user,
    user_factory,
    company_factory,
):
    owner = await user_factory(email="owner5@test.com")
    target = await user_factory(email="target2@test.com")
    other = await user_factory(email="other2@test.com")

    company = await company_factory(owner=owner, name="C-Export-User-2")
    override_current_user(owner)

    quiz, question, opt1, opt2 = await _create_quiz_with_question_and_options(
        db_session,
        company_id=company.id,
    )

    await _create_attempt_with_answer(
        db_session,
        user_id=target.id,
        company_id=company.id,
        quiz_id=quiz.id,
        question_id=question.id,
        selected_option_ids=[opt1.id],
        is_correct=True,
    )
    await _create_attempt_with_answer(
        db_session,
        user_id=other.id,
        company_id=company.id,
        quiz_id=quiz.id,
        question_id=question.id,
        selected_option_ids=[opt2.id],
        is_correct=False,
    )

    resp = await client.get(
        f"/api/v1/companies/{company.id}/users/{target.id}/quiz-attempts/export/db?format=json"
    )

    _assert_file_headers(resp, ext="json", must_contain=str(company.id))
    payload = resp.json()
    assert payload["attempts"]
    assert {a["user_id"] for a in payload["attempts"]} == {target.id}


@pytest.mark.anyio
async def test_company_user_export_db_csv_filename_contains_user_and_company(
    client,
    db_session,
    override_current_user,
    user_factory,
    company_factory,
):
    owner = await user_factory(email="owner6@test.com")
    target = await user_factory(email="target3@test.com")
    company = await company_factory(owner=owner, name="C-Export-User-CSV")

    override_current_user(owner)

    quiz, question, opt1, opt2 = await _create_quiz_with_question_and_options(
        db_session,
        company_id=company.id,
    )

    await _create_attempt_with_answer(
        db_session,
        user_id=target.id,
        company_id=company.id,
        quiz_id=quiz.id,
        question_id=question.id,
        selected_option_ids=[opt1.id],
        is_correct=True,
    )

    resp = await client.get(
        f"/api/v1/companies/{company.id}/users/{target.id}/quiz-attempts/export/db?format=csv"
    )

    cd = _assert_file_headers(resp, ext="csv", must_contain=str(company.id))
    assert f"user_{target.id}_quiz_attempts_{company.id}_" in cd
