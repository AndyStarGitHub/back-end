import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.quiz import QuizService
from app.repositories.quiz import QuizRepository
from app.schemas.quiz import (
    QuizSubmit,
    QuizAnswerSubmit,
    QuizAttemptRead,
    UserQuizStats,
)
from app.core.errors import NotFound
from tests.services.test_quiz_service import _make_valid_quiz_create


quiz_service = QuizService()
quiz_repo = QuizRepository()


@pytest.mark.asyncio
async def test_submit_quiz_success_for_non_member_user(
    db_session: AsyncSession,
    user_factory,
    company_factory,
):

    owner = await user_factory(email="owner_quiz@example.com")
    candidate = await user_factory(email="candidate@example.com")

    company = await company_factory(owner=owner)

    create_data = _make_valid_quiz_create()
    quiz_read = await quiz_service.create_quiz(
        db_session,
        company_id=company.id,
        current_user=owner,
        data=create_data,
    )

    quiz_obj = await quiz_repo.get_full_by_id(db_session, quiz_read.id)

    answers = []
    for question in quiz_obj.questions:
        correct_option_ids = [
            opt.id for opt in question.options if opt.is_correct
        ]

        assert correct_option_ids

        answers.append(
            QuizAnswerSubmit(
                question_id=question.id,
                selected_option_ids=correct_option_ids,
            )
        )

    submit_data = QuizSubmit(answers=answers)

    attempt: QuizAttemptRead = await quiz_service.submit_quiz(
        db_session,
        company_id=company.id,
        quiz_id=quiz_obj.id,
        current_user=candidate,
        data=submit_data,
    )

    assert attempt.user_id == candidate.id
    assert attempt.company_id == company.id
    assert attempt.quiz_id == quiz_obj.id

    assert attempt.total_questions == len(quiz_obj.questions)
    assert attempt.correct_answers == len(quiz_obj.questions)

    stats_company: UserQuizStats = await quiz_service.get_user_stats_for_company(
        db_session,
        company_id=company.id,
        current_user=candidate,
    )
    assert stats_company.user_id == candidate.id
    assert stats_company.total_questions_answered == attempt.total_questions
    assert stats_company.total_correct_answers == attempt.correct_answers
    assert stats_company.average_score == pytest.approx(1.0)

    stats_global: UserQuizStats = await quiz_service.get_user_stats_global(
        db_session,
        current_user=candidate,
    )
    assert stats_global.total_questions_answered == attempt.total_questions
    assert stats_global.total_correct_answers == attempt.correct_answers
    assert stats_global.average_score == pytest.approx(1.0)


@pytest.mark.asyncio
async def test_submit_quiz_requires_all_questions_answered(
    db_session: AsyncSession,
    user_factory,
    company_factory,
):

    owner = await user_factory(email="owner_partial@example.com")
    user = await user_factory(email="user_partial@example.com")

    company = await company_factory(owner=owner)

    create_data = _make_valid_quiz_create()
    quiz_read = await quiz_service.create_quiz(
        db_session,
        company_id=company.id,
        current_user=owner,
        data=create_data,
    )

    quiz_obj = await quiz_repo.get_full_by_id(db_session, quiz_read.id)

    assert len(quiz_obj.questions) >= 2

    first_question = quiz_obj.questions[0]
    correct_option_ids = [
        opt.id for opt in first_question.options if opt.is_correct
    ]
    assert correct_option_ids

    submit_data = QuizSubmit(
        answers=[
            QuizAnswerSubmit(
                question_id=first_question.id,
                selected_option_ids=correct_option_ids,
            )
        ]
    )

    with pytest.raises(NotFound) as exc_info:
        await quiz_service.submit_quiz(
            db_session,
            company_id=company.id,
            quiz_id=quiz_obj.id,
            current_user=user,
            data=submit_data,
        )

    assert "answer all questions" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_submit_quiz_invalid_option_for_question(
    db_session: AsyncSession,
    user_factory,
    company_factory,
):

    owner = await user_factory(email="owner_invalid_opt@example.com")
    user = await user_factory(email="user_invalid_opt@example.com")

    company = await company_factory(owner=owner)

    create_data = _make_valid_quiz_create()
    quiz_read = await quiz_service.create_quiz(
        db_session,
        company_id=company.id,
        current_user=owner,
        data=create_data,
    )

    quiz_obj = await quiz_repo.get_full_by_id(db_session, quiz_read.id)

    assert len(quiz_obj.questions) >= 2

    q1, q2 = quiz_obj.questions[0], quiz_obj.questions[1]

    q1_correct_ids = [opt.id for opt in q1.options if opt.is_correct]
    assert q1_correct_ids

    foreign_option_id = q2.options[0].id

    submit_data = QuizSubmit(
        answers=[
            QuizAnswerSubmit(
                question_id=q1.id,
                selected_option_ids=q1_correct_ids + [foreign_option_id],
            ),

            QuizAnswerSubmit(
                question_id=q2.id,
                selected_option_ids=[
                    opt.id for opt in q2.options if opt.is_correct
                ],
            ),
        ]
    )

    with pytest.raises(NotFound) as exc_info:
        await quiz_service.submit_quiz(
            db_session,
            company_id=company.id,
            quiz_id=quiz_obj.id,
            current_user=user,
            data=submit_data,
        )

    assert "does not belong to this question" in str(exc_info.value).lower()
