import pytest

from app.main import app
from app.core.deps import get_quiz_service

pytestmark = pytest.mark.anyio


async def test_company_quiz_analytics_weekly_happy_path_returns_200(
    client,
    override_current_user,
    user_factory,
    company_factory,
):
    owner = await user_factory(email="owner@example.com")
    company = await company_factory(owner=owner)

    override_current_user(owner)

    class FakeQuizService:
        async def get_company_weekly_stats(
                self,
                db,
                *,
                company_id,
                current_user,
                start=None,
                end=None
        ):
            return {"company_id": company_id, "items": []}

    app.dependency_overrides[get_quiz_service] = lambda: FakeQuizService()
    try:
        resp = await client.get(
            f"/api/v1/companies/{company.id}/quiz-analytics/weekly"
        )
        assert resp.status_code == 200

        data = resp.json()
        assert data["company_id"] == str(company.id)
        assert data["items"] == []
    finally:
        app.dependency_overrides.pop(get_quiz_service, None)
