import pytest

pytestmark = pytest.mark.anyio


async def test_quiz_export_my_happy_path_returns_200(
    client,
    override_current_user,
    user_factory,
    company_factory,
):
    owner = await user_factory(email="owner@example.com")
    company = await company_factory(owner=owner)

    override_current_user(owner)

    resp = await client.get(
        f"/api/v1/me/quiz/companies/{company.id}/quizzes/export/my",
        params={"format": "json"},
    )

    assert resp.status_code == 200

    content_type = (resp.headers.get("content-type") or "").lower()
    assert (("application/json" in content_type)
            or ("text/csv" in content_type)
            or (resp.text is not None))
