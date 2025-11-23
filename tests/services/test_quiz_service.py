import pytest

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import Forbidden, NotFound
from app.models.company_member import CompanyMemberRoleEnum
from app.schemas.quiz import (
    QuizCreate,
    QuizUpdate,
    QuizQuestionCreate,
    QuizAnswerOptionCreate,
)
from app.services.quiz import QuizService


quiz_service = QuizService()


def _make_valid_quiz_create() -> QuizCreate:
    return QuizCreate(
        title="Test quiz",
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


@pytest.mark.asyncio
async def test_create_quiz_by_owner_success(
    db_session: AsyncSession,
    user_factory,
    company_factory,
):

    owner = await user_factory()
    company = await company_factory(owner=owner)

    data = _make_valid_quiz_create()

    result = await quiz_service.create_quiz(
        db_session,
        company_id=company.id,
        current_user=owner,
        data=data,
    )

    assert result.id is not None
    assert result.company_id == company.id
    assert result.title == data.title
    assert len(result.questions) == 2
    assert all(len(q.options) == 2 for q in result.questions)


@pytest.mark.asyncio
async def test_create_quiz_forbidden_for_non_admin_member(
    db_session: AsyncSession,
    user_factory,
    company_factory,
    company_member_factory,
):

    owner = await user_factory(email="owner@example.com")
    member = await user_factory(email="member@example.com")

    company = await company_factory(owner=owner)

    await company_member_factory(
        company=company,
        user=member,
        role=CompanyMemberRoleEnum.MEMBER,
    )

    data = _make_valid_quiz_create()

    with pytest.raises(Forbidden):
        await quiz_service.create_quiz(
            db_session,
            company_id=company.id,
            current_user=member,
            data=data,
        )


@pytest.mark.asyncio
async def test_create_quiz_invalid_too_few_questions(
    db_session: AsyncSession,
    user_factory,
    company_factory,
):

    owner = await user_factory()
    company = await company_factory(owner=owner)

    data = QuizCreate(
        title="Invalid quiz",
        description=None,
        questions=[
            QuizQuestionCreate(
                title="Only one question",
                options=[
                    QuizAnswerOptionCreate(text="A1", is_correct=True),
                    QuizAnswerOptionCreate(text="A2", is_correct=False),
                ],
            )
        ],
    )

    with pytest.raises(NotFound) as exc_info:
        await quiz_service.create_quiz(
            db_session,
            company_id=company.id,
            current_user=owner,
            data=data,
        )

    assert "at least two questions" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_update_quiz_replaces_questions(
    db_session: AsyncSession,
    user_factory,
    company_factory,
):

    owner = await user_factory()
    company = await company_factory(owner=owner)

    create_data = _make_valid_quiz_create()
    created = await quiz_service.create_quiz(
        db_session,
        company_id=company.id,
        current_user=owner,
        data=create_data,
    )

    assert len(created.questions) == 2

    update_data = QuizUpdate(
        title="Updated quiz title",
        questions=[
            QuizQuestionCreate(
                title="New Q1",
                options=[
                    QuizAnswerOptionCreate(text="X1", is_correct=True),
                    QuizAnswerOptionCreate(text="X2", is_correct=False),
                ],
            ),
            QuizQuestionCreate(
                title="New Q2",
                options=[
                    QuizAnswerOptionCreate(text="Y1", is_correct=False),
                    QuizAnswerOptionCreate(text="Y2", is_correct=True),
                ],
            ),
            QuizQuestionCreate(
                title="New Q3",
                options=[
                    QuizAnswerOptionCreate(text="Z1", is_correct=True),
                    QuizAnswerOptionCreate(text="Z2", is_correct=False),
                ],
            ),
        ],
    )

    updated = await quiz_service.update_quiz(
        db_session,
        company_id=company.id,
        quiz_id=created.id,
        current_user=owner,
        data=update_data,
    )

    assert updated.title == "Updated quiz title"
    assert len(updated.questions) == 3
    assert {q.title for q in updated.questions} == {"New Q1", "New Q2", "New Q3"}


@pytest.mark.asyncio
async def test_list_quizzes_for_company_only_admin_can_see(
    db_session: AsyncSession,
    user_factory,
    company_factory,
    company_member_factory,
):

    owner = await user_factory(email="owner@example.com")
    member = await user_factory(email="member@example.com")
    admin_user = await user_factory(email="admin@example.com")

    company = await company_factory(owner=owner)

    await company_member_factory(
        company=company,
        user=member,
        role=CompanyMemberRoleEnum.MEMBER,
    )

    await company_member_factory(
        company=company,
        user=admin_user,
        role=CompanyMemberRoleEnum.ADMIN,
    )

    data = _make_valid_quiz_create()
    await quiz_service.create_quiz(
        db_session,
        company_id=company.id,
        current_user=owner,
        data=data,
    )

    resp_owner = await quiz_service.list_quizzes_for_company(
        db_session,
        company_id=company.id,
        current_user=owner,
        offset=0,
        limit=50,
    )
    assert resp_owner.total == 1
    assert len(resp_owner.items) == 1

    resp_admin = await quiz_service.list_quizzes_for_company(
        db_session,
        company_id=company.id,
        current_user=admin_user,
        offset=0,
        limit=50,
    )
    assert resp_admin.total == 1
    assert len(resp_admin.items) == 1

    with pytest.raises(Forbidden):
        await quiz_service.list_quizzes_for_company(
            db_session,
            company_id=company.id,
            current_user=member,
            offset=0,
            limit=50,
        )


@pytest.mark.asyncio
async def test_delete_quiz(
    db_session: AsyncSession,
    user_factory,
    company_factory,
):

    owner = await user_factory()
    company = await company_factory(owner=owner)

    data = _make_valid_quiz_create()
    created = await quiz_service.create_quiz(
        db_session,
        company_id=company.id,
        current_user=owner,
        data=data,
    )

    assert created.id is not None

    await quiz_service.delete_quiz(
        db_session,
        company_id=company.id,
        quiz_id=created.id,
        current_user=owner,
    )

    from app.core.errors import NotFound

    with pytest.raises(NotFound):
        await quiz_service.get_quiz(
            db_session,
            company_id=company.id,
            quiz_id=created.id,
            current_user=owner,
        )


@pytest.mark.asyncio
async def test_create_quiz_invalid_question_with_too_few_options(
    db_session: AsyncSession,
    user_factory,
    company_factory,
):

    owner = await user_factory(email="owner_q_opts@example.com")
    company = await company_factory(owner=owner)

    data = _make_valid_quiz_create()

    data.questions[0].options = [
        QuizAnswerOptionCreate(text="only one", is_correct=True),
    ]

    with pytest.raises(NotFound) as exc_info:
        await quiz_service.create_quiz(
            db_session,
            company_id=company.id,
            current_user=owner,
            data=data,
        )

    assert "at least two answer options" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_create_quiz_invalid_question_without_correct_answer(
    db_session: AsyncSession,
    user_factory,
    company_factory,
):

    owner = await user_factory(email="owner_no_correct@example.com")
    company = await company_factory(owner=owner)

    data = _make_valid_quiz_create()

    data.questions[1].options = [
        QuizAnswerOptionCreate(text="opt1", is_correct=False),
        QuizAnswerOptionCreate(text="opt2", is_correct=False),
    ]

    with pytest.raises(NotFound) as exc_info:
        await quiz_service.create_quiz(
            db_session,
            company_id=company.id,
            current_user=owner,
            data=data,
        )

    assert "each question must have at least one correct answer" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_create_quiz_by_admin_success(
    db_session: AsyncSession,
    user_factory,
    company_factory,
    company_member_factory,
):

    owner = await user_factory(email="owner_for_admin_create@example.com")
    admin_user = await user_factory(email="admin_for_admin_create@example.com")

    company = await company_factory(owner=owner)

    await company_member_factory(
        company=company,
        user=admin_user,
        role=CompanyMemberRoleEnum.ADMIN,
    )

    data = _make_valid_quiz_create()

    result = await quiz_service.create_quiz(
        db_session,
        company_id=company.id,
        current_user=admin_user,
        data=data,
    )

    assert result.id is not None
    assert result.company_id == company.id
    assert result.title == data.title
    assert len(result.questions) == 2


@pytest.mark.asyncio
async def test_update_quiz_invalid_too_few_questions(
    db_session: AsyncSession,
    user_factory,
    company_factory,
):

    owner = await user_factory(email="owner_update_invalid@example.com")
    company = await company_factory(owner=owner)

    create_data = _make_valid_quiz_create()
    created = await quiz_service.create_quiz(
        db_session,
        company_id=company.id,
        current_user=owner,
        data=create_data,
    )

    update_data = QuizUpdate(
        questions=[
            QuizQuestionCreate(
                title="Only one question in update",
                options=[
                    QuizAnswerOptionCreate(text="opt1", is_correct=True),
                    QuizAnswerOptionCreate(text="opt2", is_correct=False),
                ],
            )
        ]
    )

    with pytest.raises(NotFound) as exc_info:
        await quiz_service.update_quiz(
            db_session,
            company_id=company.id,
            quiz_id=created.id,
            current_user=owner,
            data=update_data,
        )

    assert "at least two questions" in str(exc_info.value).lower()
