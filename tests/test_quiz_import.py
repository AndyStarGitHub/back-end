import io
import pytest
from openpyxl import Workbook
from sqlalchemy import select

from app.models.quiz import Quiz, QuizQuestion, QuizAnswerOption
from app.models.company_member import CompanyMemberRoleEnum

from app.main import app
from app.core.deps import get_quiz_service
from app.services.quiz import QuizService


IMPORT_URL = "/api/v1/me/quiz/companies/{company_id}/quizzes/import"


@pytest.fixture(autouse=True)
def override_quiz_service_dependency():
    async def _get_quiz_service_override():
        return QuizService(quiz_redis_repo=None)

    app.dependency_overrides[get_quiz_service] = _get_quiz_service_override
    yield
    app.dependency_overrides.pop(get_quiz_service, None)

def make_xlsx(rows: list[list], *, sheet_name: str = "Quizzes") -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = sheet_name
    for r in rows:
        ws.append(r)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def multipart_xlsx(file_bytes: bytes, filename: str = "quizzes.xlsx"):
    return {
        "file": (
            filename,
            file_bytes,
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    }


@pytest.mark.anyio
async def test_import_create_quiz_success(
    client,
    db_session,
    override_current_user,
    user_factory,
    company_factory,
):
    owner = await user_factory(email="owner1@example.com")
    company = await company_factory(owner=owner, name="C1")
    override_current_user(owner)

    xlsx = make_xlsx([
        ["quiz_id", "quiz_title", "quiz_description", "quiz_frequency", "question_title", "option_text", "is_correct"],
        ["", "Math basics", "desc", "quarterly", "2+2?", "4", True],
        ["", "Math basics", "desc", "quarterly", "2+2?", "5", False],
        ["", "Math basics", "desc", "quarterly", "3+3?", "6", True],
        ["", "Math basics", "desc", "quarterly", "3+3?", "7", False],
    ])

    resp = await client.post(
        IMPORT_URL.format(company_id=company.id),
        files=multipart_xlsx(xlsx),
    )

    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["created"] == 1
    assert data["updated"] == 0
    assert data["total_in_file"] == 1

    res = await db_session.execute(select(Quiz).
                                   where(Quiz.company_id == company.id)
                                   )
    quizzes = list(res.scalars().all())
    assert len(quizzes) == 1
    assert quizzes[0].title == "Math basics"


@pytest.mark.anyio
async def test_import_update_by_title_replaces_questions(
    client,
    db_session,
    override_current_user,
    user_factory,
    company_factory,
):
    owner = await user_factory(email="owner2@example.com")
    company = await company_factory(owner=owner, name="C2")
    override_current_user(owner)

    xlsx1 = make_xlsx([
        ["quiz_id", "quiz_title", "quiz_description", "quiz_frequency", "question_title", "option_text", "is_correct"],
        ["", "Security", "d1", "monthly", "Q1", "A", True],
        ["", "Security", "d1", "monthly", "Q1", "B", False],
        ["", "Security", "d1", "monthly", "Q2", "C", True],
        ["", "Security", "d1", "monthly", "Q2", "D", False],
    ])
    r1 = await client.post(
        IMPORT_URL.format(company_id=company.id),
        files=multipart_xlsx(xlsx1, "s1.xlsx"),
    )
    assert r1.status_code == 200, r1.text
    assert r1.json()["created"] == 1

    xlsx2 = make_xlsx([
        ["quiz_id", "quiz_title", "quiz_description", "quiz_frequency", "question_title", "option_text", "is_correct"],
        ["", "Security", "d2", "quarterly", "NEW_Q1", "X", True],
        ["", "Security", "d2", "quarterly", "NEW_Q1", "Y", False],
        ["", "Security", "d2", "quarterly", "NEW_Q2", "Z", True],
        ["", "Security", "d2", "quarterly", "NEW_Q2", "W", False],
    ])
    r2 = await client.post(
        IMPORT_URL.format(company_id=company.id),
        files=multipart_xlsx(xlsx2, "s2.xlsx"),
    )
    assert r2.status_code == 200, r2.text
    body = r2.json()
    assert body["created"] == 0
    assert body["updated"] == 1

    qres = await db_session.execute(
        select(Quiz).
        where(Quiz.company_id == company.id, Quiz.title == "Security")
    )
    quiz = qres.scalars().first()
    assert quiz is not None

    full = await db_session.execute(
        select(Quiz)
        .where(Quiz.id == quiz.id)
    )
    q_q = await db_session.execute(select(QuizQuestion).
                                   where(QuizQuestion.quiz_id == quiz.id)
                                   )
    questions = list(q_q.scalars().all())
    assert {q.title for q in questions} == {"NEW_Q1", "NEW_Q2"}

    assert len(questions) == 2
    q_ids = [q.id for q in questions]
    opt_q = await db_session.execute(select(QuizAnswerOption).
                                     where(
                                        QuizAnswerOption.question_id.in_(q_ids)
                                        )
                                     )
    options = list(opt_q.scalars().all())
    assert len(options) == 4


@pytest.mark.anyio
async def test_import_validation_fails_one_option_one_question_returns_422_and_rolls_back(
    client,
    db_session,
    override_current_user,
    user_factory,
    company_factory,
):
    owner = await user_factory(email="owner3@example.com")
    company = await company_factory(owner=owner, name="C3")
    company_id = company.id
    override_current_user(owner)

    bad = make_xlsx([
        ["quiz_id", "quiz_title", "quiz_description", "quiz_frequency", "question_title", "option_text", "is_correct"],
        ["", "Bad Quiz", "desc", "monthly", "Only Q", "Only A", True],
    ])

    resp = await client.post(
        IMPORT_URL.format(company_id=company_id),
        files=multipart_xlsx(bad, "bad.xlsx"),
    )

    assert resp.status_code == 422, resp.text
    detail = resp.json().get("detail")
    assert isinstance(detail, list) and detail, detail

    res = await db_session.execute(select(Quiz).
                                   where(Quiz.company_id == company_id)
                                   )
    quizzes = list(res.scalars().all())
    assert len(quizzes) == 0


@pytest.mark.anyio
async def test_import_all_or_nothing_if_one_quiz_invalid_none_saved(
    client,
    db_session,
    override_current_user,
    user_factory,
    company_factory,
):
    owner = await user_factory(email="owner4@example.com")
    company = await company_factory(owner=owner, name="C4")
    company_id = company.id
    override_current_user(owner)

    mixed = make_xlsx([
        ["quiz_id", "quiz_title", "quiz_description", "quiz_frequency", "question_title", "option_text", "is_correct"],

        ["", "Good", "d", "monthly", "Q1", "A", True],
        ["", "Good", "d", "monthly", "Q1", "B", False],
        ["", "Good", "d", "monthly", "Q2", "C", True],
        ["", "Good", "d", "monthly", "Q2", "D", False],

        ["", "Bad", "d", "monthly", "QQ", "X", True],
    ])

    resp = await client.post(
        IMPORT_URL.format(company_id=company_id),
        files=multipart_xlsx(mixed, "mixed.xlsx"),
    )

    assert resp.status_code == 422, resp.text

    res = await db_session.execute(select(Quiz).
                                   where(Quiz.company_id == company_id)
                                   )
    titles = {q.title for q in res.scalars().all()}
    assert "Good" not in titles
    assert "Bad" not in titles


@pytest.mark.anyio
async def test_import_forbidden_for_member(
    client,
    override_current_user,
    user_factory,
    company_factory,
    company_member_factory,
):
    owner = await user_factory(email="owner5@example.com")
    member = await user_factory(email="member5@example.com")
    company = await company_factory(owner=owner, name="C5")
    await company_member_factory(
        company=company,
        user=member,
        role=CompanyMemberRoleEnum.MEMBER
    )

    override_current_user(member)

    xlsx = make_xlsx([
        ["quiz_id", "quiz_title", "quiz_description", "quiz_frequency", "question_title", "option_text", "is_correct"],
        ["", "Any", "d", "monthly", "Q1", "A", True],
        ["", "Any", "d", "monthly", "Q1", "B", False],
        ["", "Any", "d", "monthly", "Q2", "C", True],
        ["", "Any", "d", "monthly", "Q2", "D", False],
    ])

    resp = await client.post(
        IMPORT_URL.format(company_id=company.id),
        files=multipart_xlsx(xlsx, "forbidden.xlsx"),
    )

    assert resp.status_code == 403, resp.text
