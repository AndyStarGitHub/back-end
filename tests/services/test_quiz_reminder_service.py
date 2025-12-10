import pytest
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.quiz import QuizService
from app.services.quiz_reminder import QuizReminderService
from app.repositories.notification import NotificationRepository
from app.schemas.quiz import (
    QuizCreate,
    QuizQuestionCreate,
    QuizAnswerOptionCreate,
    QuizSubmit,
)

quiz_service = QuizService()
reminder_service = QuizReminderService()
notification_repo = NotificationRepository()


def _make_valid_quiz_create(title: str = "Test quiz") -> QuizCreate:

    return QuizCreate(
        title=title,
        description="Some description",
        questions=[
            QuizQuestionCreate(
                title="Question 1",
                options=[
                    QuizAnswerOptionCreate(text="A1", is_correct=True),
                    QuizAnswerOptionCreate(text="A2", is_correct=False),
                ],
            ),
            QuizQuestionCreate(
                title="Question 2",
                options=[
                    QuizAnswerOptionCreate(text="B1", is_correct=False),
                    QuizAnswerOptionCreate(text="B2", is_correct=True),
                ],
            ),
        ],
    )


def _make_quiz_submit_from_quiz_read(quiz_read) -> QuizSubmit:

    answers: list[dict] = []

    for q in quiz_read.questions:
        first_option_id = q.options[0].id
        answers.append(
            {
                "question_id": q.id,
                "selected_option_ids": [first_option_id],
            }
        )

    return QuizSubmit(answers=answers)


@pytest.mark.asyncio
async def test_run_daily_reminders_creates_notifications_for_overdue_quizzes(
    db_session: AsyncSession,
    user_factory,
    company_factory,
    company_member_factory,
):

    owner = await user_factory(email="owner_reminder@example.com")
    member = await user_factory(email="member_reminder@example.com")

    company = await company_factory(owner=owner)

    await company_member_factory(
        company=company,
        user=member,
    )

    quiz1_data = _make_valid_quiz_create(title="Quiz 1")
    quiz2_data = _make_valid_quiz_create(title="Quiz 2")

    quiz1_read = await quiz_service.create_quiz(
        db_session,
        company_id=company.id,
        current_user=owner,
        data=quiz1_data,
    )

    quiz2_read = await quiz_service.create_quiz(
        db_session,
        company_id=company.id,
        current_user=owner,
        data=quiz2_data,
    )

    quiz1_submit = _make_quiz_submit_from_quiz_read(quiz1_read)

    await quiz_service.submit_quiz(
        db_session,
        company_id=company.id,
        quiz_id=quiz1_read.id,
        current_user=member,
        data=quiz1_submit,
    )

    now = datetime.utcnow()
    await reminder_service.run_daily_reminders(
        db_session,
        period_hours=24 * 365,
        now_utc=now,
    )

    total_owner, owner_notifs = await notification_repo.get_paginated_for_user(
        db_session,
        user_id=owner.id,
        offset=0,
        limit=20,
    )

    owner_reminders = [
        n for n in owner_notifs
        if "You have not completed the following quizzes" in n.message
    ]

    assert len(owner_reminders) == 1
    owner_msg = owner_reminders[0].message
    assert "Quiz 1" in owner_msg
    assert "Quiz 2" in owner_msg

    total_member, member_notifs = await notification_repo.get_paginated_for_user(
        db_session,
        user_id=member.id,
        offset=0,
        limit=20,
    )

    member_reminders = [
        n for n in member_notifs
        if "You have not completed the following quizzes" in n.message
    ]

    assert len(member_reminders) == 1
    member_msg = member_reminders[0].message

    assert "Quiz 1" not in member_msg
    assert "Quiz 2" in member_msg


@pytest.mark.asyncio
async def test_run_daily_reminders_no_notifications_if_all_quizzes_completed(
    db_session: AsyncSession,
    user_factory,
    company_factory,
):

    owner = await user_factory(email="owner_all_done@example.com")
    company = await company_factory(owner=owner)

    quiz_data = _make_valid_quiz_create(title="Only Quiz")

    quiz_read = await quiz_service.create_quiz(
        db_session,
        company_id=company.id,
        current_user=owner,
        data=quiz_data,
    )

    submit_data = _make_quiz_submit_from_quiz_read(quiz_read)
    await quiz_service.submit_quiz(
        db_session,
        company_id=company.id,
        quiz_id=quiz_read.id,
        current_user=owner,
        data=submit_data,
    )

    now = datetime.utcnow()
    await reminder_service.run_daily_reminders(
        db_session,
        period_hours=24 * 365,
        now_utc=now,
    )

    total_owner, owner_notifs = await notification_repo.get_paginated_for_user(
        db_session,
        user_id=owner.id,
        offset=0,
        limit=10,
    )
    assert total_owner == 0
    assert owner_notifs == []
