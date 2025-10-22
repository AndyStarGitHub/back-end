from fastapi import FastAPI
from fastapi.responses import JSONResponse
from app.core.config import settings

app = FastAPI(title=settings.APP_NAME)


@app.get("/", response_class=JSONResponse)
def health_check() -> JSONResponse:
    payload = {"status_code": 200, "detail": "ok", "result": "working"}
    return JSONResponse(content=payload, status_code=200)
