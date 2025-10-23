from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(tags=["health"])


@router.get("/", response_class=JSONResponse)
def health_check() -> JSONResponse:
    payload = {"status_code": 200, "detail": "ok", "result": "working"}
    return JSONResponse(content=payload, status_code=200)
