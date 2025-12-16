import pytest

from app.main import app
from app.core.deps import get_quiz_service

pytestmark = pytest.mark.anyio


async def test_quiz_export_my_happy_path_returns_200_and_attachment_header(
    client,
    override_current_user,
    user_factory,
    company_factory,
):
    user = await user_factory(email="me@example.com")
    company = await company_factory(owner=user)
    override_current_user(user)

    class FakeQuizService:
        async def export_my_attempts_for_company(
            self, db, *, company_id, current_user, format="json", quiz_id=None
        ):
            return [] if format == "json" else ""

    app.dependency_overrides[get_quiz_service] = lambda: FakeQuizService()
    try:
        resp = await client.get(
            f"/api/v1/me/quiz/companies/{company.id}/quizzes/export/my",
            params={"format": "json"},
        )

        assert resp.status_code == 200
        cd = (resp.headers.get("content-disposition") or "").lower()
        assert "attachment" in cd
        assert f"quiz_export_my_{company.id}.json" in cd
    finally:
        app.dependency_overrides.pop(get_quiz_service, None)


async def test_quiz_export_user_happy_path_returns_200_and_attachment_header(
    client,
    override_current_user,
    user_factory,
    company_factory,
):
    owner = await user_factory(email="owner@example.com")
    target = await user_factory(email="target@example.com")
    company = await company_factory(owner=owner)
    override_current_user(owner)

    class FakeQuizService:
        async def export_user_attempts_for_company(
            self,
                db,
                *,
                company_id,
                current_user,
                target_user_id,
                format="json",
                quiz_id=None
        ):
            return [] if format == "json" else ""

    app.dependency_overrides[get_quiz_service] = lambda: FakeQuizService()
    try:
        resp = await client.get(
            f"/api/v1/me/quiz/companies/{company.id}/quizzes/export/users/{target.id}",
            params={"format": "json"},
        )

        assert resp.status_code == 200
        cd = (resp.headers.get("content-disposition") or "").lower()
        assert "attachment" in cd
        assert f"quiz_export_user_{target.id}_company_{company.id}.json" in cd
    finally:
        app.dependency_overrides.pop(get_quiz_service, None)


async def test_quiz_export_my_csv_happy_path_returns_200_and_csv_headers(
    client,
    override_current_user,
    user_factory,
    company_factory,
):
    user = await user_factory(email="me@example.com")
    company = await company_factory(owner=user)
    override_current_user(user)

    class FakeQuizService:
        async def export_my_attempts_for_company(
            self, db, *, company_id, current_user, format="csv", quiz_id=None
        ):
            return "col1,col2\n"

    from app.main import app
    from app.core.deps import get_quiz_service

    app.dependency_overrides[get_quiz_service] = lambda: FakeQuizService()
    try:
        resp = await client.get(
            f"/api/v1/me/quiz/companies/{company.id}/quizzes/export/my",
            params={"format": "csv"},
        )

        assert resp.status_code == 200

        ct = (resp.headers.get("content-type") or "").lower()
        assert "text/csv" in ct

        cd = (resp.headers.get("content-disposition") or "").lower()
        assert "attachment" in cd
        assert f'quiz_export_my_{company.id}.csv' in cd
    finally:
        app.dependency_overrides.pop(get_quiz_service, None)


async def test_quiz_export_user_csv_happy_path_returns_200_and_csv_headers(
    client,
    override_current_user,
    user_factory,
    company_factory,
):
    owner = await user_factory(email="owner@example.com")
    target = await user_factory(email="target@example.com")
    company = await company_factory(owner=owner)
    override_current_user(owner)

    class FakeQuizService:
        async def export_user_attempts_for_company(
            self,
                db,
                *,
                company_id,
                current_user,
                target_user_id,
                format="csv",
                quiz_id=None
        ):
            return "a,b\n"

    from app.main import app
    from app.core.deps import get_quiz_service

    app.dependency_overrides[get_quiz_service] = lambda: FakeQuizService()
    try:
        resp = await client.get(
            f"/api/v1/me/quiz/companies/{company.id}/quizzes/export/users/{target.id}",
            params={"format": "csv"},
        )

        assert resp.status_code == 200

        ct = (resp.headers.get("content-type") or "").lower()
        assert "text/csv" in ct

        cd = (resp.headers.get("content-disposition") or "").lower()
        assert "attachment" in cd
        assert f'quiz_export_user_{target.id}_company_{company.id}.csv' in cd
    finally:
        app.dependency_overrides.pop(get_quiz_service, None)
