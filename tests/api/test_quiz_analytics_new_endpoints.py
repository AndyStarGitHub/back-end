from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import event

from app.models.quiz import Quiz
from app.models.quiz_attempt import QuizAttempt
from app.models.company_member import CompanyMemberRoleEnum


@pytest.fixture()
def sqlite_date_trunc(engine):
    def _utc(dt: datetime) -> datetime:
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)

    def _date_trunc(unit: str, value):
        if value is None:
            return None
        unit = (unit or "").lower()

        if isinstance(value, datetime):
            dt = value
        else:
            s = str(value)
            if s.endswith("Z"):
                s = s[:-1] + "+00:00"
            try:
                dt = datetime.fromisoformat(s)
            except ValueError:
                dt = datetime.strptime(s.split(".")[0], "%Y-%m-%d %H:%M:%S")

        dt = _utc(dt)

        if unit == "week":
            start = (dt - timedelta(days=dt.weekday())).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            return start.isoformat()

        return dt.replace(microsecond=0).isoformat()

    @event.listens_for(engine.sync_engine, "connect")
    def _on_connect(dbapi_conn, _):
        dbapi_conn.create_function("date_trunc", 2, _date_trunc)

    return True


async def _create_quiz(db_session, *, company_id, title: str = "Q") -> Quiz:
    q = Quiz(
        company_id=company_id,
        title=title,
        description="",
        frequency="monthly",
    )
    db_session.add(q)
    await db_session.commit()
    await db_session.refresh(q)
    return q


async def _create_attempt(
    db_session,
    *,
    user_id: int,
    company_id,
    quiz_id,
    total_questions: int,
    correct_answers: int,
    created_at: datetime | None = None,
) -> QuizAttempt:
    a = QuizAttempt(
        user_id=user_id,
        company_id=company_id,
        quiz_id=quiz_id,
        total_questions=total_questions,
        correct_answers=correct_answers,
    )
    if created_at is not None:
        a.created_at = created_at
    db_session.add(a)
    await db_session.commit()
    await db_session.refresh(a)
    return a


def _utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


@pytest.mark.anyio
async def test_general_rating_empty_returns_zeros(client):
    resp = await client.get("/api/v1/quiz_analytics/general-rating")
    assert resp.status_code == 200
    data = resp.json()

    assert data["total_questions"] == 0
    assert data["total_correct_answers"] == 0
    assert data["attempts_count"] == 0
    assert data["average_score"] == 0.0


@pytest.mark.anyio
async def test_general_rating_aggregates_correctly(
    client,
    db_session,
    user_factory,
    company_factory,
):
    user = await user_factory(email="a@test.com")
    company = await company_factory(owner=user, name="C1")
    quiz = await _create_quiz(db_session, company_id=company.id, title="Q1")

    await _create_attempt(
        db_session,
        user_id=user.id,
        company_id=company.id,
        quiz_id=quiz.id,
        total_questions=10,
        correct_answers=7,
    )
    await _create_attempt(
        db_session,
        user_id=user.id,
        company_id=company.id,
        quiz_id=quiz.id,
        total_questions=0,
        correct_answers=0,
    )

    resp = await client.get("/api/v1/quiz_analytics/general-rating")
    assert resp.status_code == 200
    data = resp.json()

    assert data["total_questions"] == 10
    assert data["total_correct_answers"] == 7
    assert data["attempts_count"] == 2
    assert data["average_score"] == 7 / 10


@pytest.mark.anyio
async def test_general_rating_still_works_when_auth_override_is_set(
    client,
    override_current_user,
    user_factory,
):
    user = await user_factory(email="auth@test.com")
    override_current_user(user)

    resp = await client.get("/api/v1/quiz_analytics/general-rating")
    assert resp.status_code == 200
    assert "average_score" in resp.json()


@pytest.mark.anyio
async def test_me_weekly_requires_auth(
        client,
        override_current_user,
        sqlite_date_trunc
):
    override_current_user(None)

    resp = await client.get("/api/v1/me/quiz_analytics/weekly")
    assert resp.status_code == 401


@pytest.mark.anyio
async def test_me_weekly_groups_by_quiz_and_week(
    client,
    db_session,
    override_current_user,
    user_factory,
    company_factory,
    sqlite_date_trunc,
):
    user = await user_factory(email="me@test.com")
    override_current_user(user)

    company = await company_factory(owner=user, name="C2")
    quiz1 = await _create_quiz(
        db_session,
        company_id=company.id,
        title="Quiz A"
    )
    quiz2 = await _create_quiz(
        db_session,
        company_id=company.id,
        title="Quiz B"
    )

    base = _utc(datetime(2025, 12, 29, 10, 0, 0))

    await _create_attempt(
        db_session,
        user_id=user.id,
        company_id=company.id,
        quiz_id=quiz1.id,
        total_questions=10,
        correct_answers=8,
        created_at=base
    )
    await _create_attempt(
        db_session,
        user_id=user.id,
        company_id=company.id,
        quiz_id=quiz1.id,
        total_questions=5,
        correct_answers=4,
        created_at=base + timedelta(days=1)
    )
    await _create_attempt(
        db_session,
        user_id=user.id,
        company_id=company.id,
        quiz_id=quiz2.id,
        total_questions=4,
        correct_answers=2,
        created_at=base + timedelta(days=2)
    )

    resp = await client.get("/api/v1/me/quiz_analytics/weekly")
    assert resp.status_code == 200
    data = resp.json()

    assert data["user_id"] == user.id
    items = data["items"]
    assert len(items) == 2

    i1 = next(i for i in items if i["quiz_id"] == str(quiz1.id))
    assert i1["total_questions"] == 15
    assert i1["total_correct_answers"] == 12
    assert i1["attempts_count"] == 2
    assert i1["average_score"] == 12 / 15
    assert "00:00:00" in i1["week_start"]

    i2 = next(i for i in items if i["quiz_id"] == str(quiz2.id))
    assert i2["total_questions"] == 4
    assert i2["total_correct_answers"] == 2
    assert i2["attempts_count"] == 1
    assert i2["average_score"] == 2 / 4


@pytest.mark.anyio
async def test_me_weekly_applies_start_end_filters(
    client,
    db_session,
    override_current_user,
    user_factory,
    company_factory,
    sqlite_date_trunc,
):
    user = await user_factory(email="filter@test.com")
    override_current_user(user)

    company = await company_factory(owner=user, name="C3")
    quiz = await _create_quiz(db_session, company_id=company.id, title="Quiz F")

    dt1 = _utc(datetime(2025, 12, 1, 12, 0, 0))
    dt2 = _utc(datetime(2025, 12, 15, 12, 0, 0))

    await _create_attempt(
        db_session,
        user_id=user.id,
        company_id=company.id,
        quiz_id=quiz.id,
        total_questions=10,
        correct_answers=5,
        created_at=dt1
    )
    await _create_attempt(
        db_session,
        user_id=user.id,
        company_id=company.id,
        quiz_id=quiz.id,
        total_questions=10,
        correct_answers=10,
        created_at=dt2
    )

    start = "2025-12-10T00:00:00Z"
    end = "2025-12-20T23:59:59Z"

    resp = await client.get(
        f"/api/v1/me/quiz_analytics/weekly?start={start}&end={end}"
    )
    assert resp.status_code == 200
    data = resp.json()

    items = data["items"]
    assert len(items) == 1
    item = items[0]
    assert item["total_questions"] == 10
    assert item["total_correct_answers"] == 10
    assert item["average_score"] == 1.0


@pytest.mark.anyio
async def test_company_last_attempts_forbidden_for_member(
    client,
    override_current_user,
    user_factory,
    company_factory,
    company_member_factory,
):
    owner = await user_factory(email="owner@test.com")
    member = await user_factory(email="member@test.com")
    company = await company_factory(owner=owner, name="C4")

    await company_member_factory(
        company=company,
        user=member,
        role=CompanyMemberRoleEnum.MEMBER
    )

    override_current_user(member)

    resp = await client.get(
        f"/api/v1/companies/{company.id}/quiz-analytics/quizzes/last-attempts"
    )
    assert resp.status_code == 403


@pytest.mark.anyio
async def test_company_last_attempts_includes_quizzes_with_null(
    client,
    db_session,
    override_current_user,
    user_factory,
    company_factory,
):
    owner = await user_factory(email="owner2@test.com")
    company = await company_factory(owner=owner, name="C5")

    override_current_user(owner)

    quiz1 = await _create_quiz(db_session, company_id=company.id, title="Q1")
    quiz2 = await _create_quiz(db_session, company_id=company.id, title="Q2")

    dt = _utc(datetime(2025, 12, 29, 18, 10, 22))
    await _create_attempt(
        db_session,
        user_id=owner.id,
        company_id=company.id,
        quiz_id=quiz1.id,
        total_questions=3,
        correct_answers=3,
        created_at=dt,
    )

    resp = await client.get(
        f"/api/v1/companies/{company.id}/quiz-analytics/quizzes/last-attempts"
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["company_id"] == str(company.id)
    items = data["items"]
    assert {i["quiz_id"] for i in items} == {str(quiz1.id), str(quiz2.id)}

    i1 = next(i for i in items if i["quiz_id"] == str(quiz1.id))
    i2 = next(i for i in items if i["quiz_id"] == str(quiz2.id))

    assert i1["last_attempt_at"] is not None
    assert i2["last_attempt_at"] is None


@pytest.mark.anyio
async def test_company_last_attempts_returns_max_created_at(
    client,
    db_session,
    override_current_user,
    user_factory,
    company_factory,
):
    owner = await user_factory(email="owner3@test.com")
    company = await company_factory(owner=owner, name="C6")

    override_current_user(owner)

    quiz = await _create_quiz(db_session, company_id=company.id, title="QMax")

    dt1 = _utc(datetime(2025, 12, 1, 10, 0, 0))
    dt2 = _utc(datetime(2025, 12, 29, 18, 10, 22))

    await _create_attempt(
        db_session,
        user_id=owner.id,
        company_id=company.id,
        quiz_id=quiz.id,
        total_questions=5,
        correct_answers=3,
        created_at=dt1
    )
    await _create_attempt(
        db_session,
        user_id=owner.id,
        company_id=company.id,
        quiz_id=quiz.id,
        total_questions=5,
        correct_answers=5,
        created_at=dt2
    )

    resp = await client.get(
        f"/api/v1/companies/{company.id}/quiz-analytics/quizzes/last-attempts"
    )
    assert resp.status_code == 200
    data = resp.json()

    item = next(i for i in data["items"] if i["quiz_id"] == str(quiz.id))
    assert item["last_attempt_at"] is not None
    assert "2025-12-29" in item["last_attempt_at"]
