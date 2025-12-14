import pytest

from app.main import app
from app.core.deps import get_quiz_service

pytestmark = pytest.mark.anyio


async def test_me_quiz_export_company_happy_path_returns_200(
    client,
    override_current_user,
    user_factory,
    company_factory,
):
    owner = await user_factory(email="me@example.com")
    company = await company_factory(owner=owner)

    override_current_user(owner)

    class FakeQuizService:
        async def export_company_attempts(
                self,
                db,
                *,
                company_id,
                current_user,
                format="json",
                quiz_id=None
        ):
            return [] if format == "json" else ""

    app.dependency_overrides[get_quiz_service] = lambda: FakeQuizService()
    try:
        resp = await client.get(
            f"/api/v1/me/quiz/companies/{company.id}/quizzes/export/company",
            params={"format": "json"},
        )

        assert resp.status_code == 200
        assert resp.headers.get("content-disposition")
    finally:
        app.dependency_overrides.pop(get_quiz_service, None)
