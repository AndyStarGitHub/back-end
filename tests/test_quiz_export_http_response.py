from fastapi.responses import JSONResponse, Response

from app.api.quizzes import _build_export_http_response


def test_build_export_http_response_json_returns_attachment_file():

    payload = {
        "company_id": "123",
        "filter": {"user_id": 1},
        "attempts": [],
    }
    filename = "quiz_export_my_123.json"

    response = _build_export_http_response(
        format="json",
        result=payload,
        filename=filename,
    )

    assert isinstance(response, JSONResponse)

    content_disposition = response.headers.get("content-disposition") or ""
    content_disposition_lower = content_disposition.lower()
    assert "attachment" in content_disposition_lower
    assert filename in content_disposition

    content_type = response.headers.get("content-type") or ""
    assert "application/json" in content_type


def test_build_export_http_response_csv_returns_attachment_csv_file():

    csv_content = "attempt_id,user_id\n1,123\n"
    filename = "quiz_export_my_123.csv"

    response = _build_export_http_response(
        format="csv",
        result=csv_content,
        filename=filename,
    )

    assert isinstance(response, Response)
    assert response.media_type == "text/csv"

    content_disposition = response.headers.get("content-disposition") or ""
    content_disposition_lower = content_disposition.lower()
    assert "attachment" in content_disposition_lower
    assert filename in content_disposition

    assert response.body == csv_content.encode()
