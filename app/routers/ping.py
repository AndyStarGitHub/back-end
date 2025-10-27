from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.db.database import get_db
from app.services.redis_client import get_redis

router = APIRouter()
log = logging.getLogger(__name__)

@router.get("/db", response_class=JSONResponse)
async def ping_db(db: AsyncSession = Depends(get_db)) -> JSONResponse:
    try:
        res = await db.execute(text("SELECT 1"))
        ok = (res.scalar() == 1)
        return JSONResponse(content={"postgres_ok": ok}, status_code=200 if ok else 503)
    except Exception as e:
        log.exception("DB ping failed: %s", e)
        return JSONResponse(content={"postgres_ok": False, "error": "database_unavailable"}, status_code=503)

@router.get("/redis", response_class=JSONResponse)
async def ping_redis() -> JSONResponse:
    try:
        redis = await get_redis()
        pong = await redis.ping()
        ok = bool(pong)
        return JSONResponse(content={"redis_ok": ok}, status_code=200 if ok else 503)
    except Exception as e:
        log.exception("Redis ping failed: %s", e)
        return JSONResponse(content={"redis_ok": False, "error": "redis_unavailable"}, status_code=503)
