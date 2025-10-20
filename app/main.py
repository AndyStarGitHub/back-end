from typing import Dict

from fastapi import FastAPI
from app.core.config import settings

app = FastAPI(title=settings.APP_NAME)


@app.get("/")
def health_check() -> Dict:
    return {"status_code": 200, "detail": "ok", "result": "working"}
