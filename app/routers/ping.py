from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.services.redis_client import get_redis

router = APIRouter(prefix="/ping", tags=["diagnostics"])


@router.get("/db", response_class=JSONResponse)
async def ping_db(db: AsyncSession = Depends(get_db)) -> JSONResponse:
    res = await db.execute(text("SELECT 1"))
    ok = (res.scalar() == 1)
    return JSONResponse(content={"postgres_ok": ok}, status_code=200)


@router.get("/redis", response_class=JSONResponse)
async def ping_redis() -> JSONResponse:
    redis = await get_redis()
    pong = await redis.ping()
    return JSONResponse(content={"redis_ok": bool(pong)}, status_code=200)
