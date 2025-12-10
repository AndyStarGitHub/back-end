from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from starlette.requests import Request
from starlette.responses import JSONResponse

from app.core.config import settings
from app.core.error_handlers import register_exception_handlers
from app.core.errors import NotFound, Conflict
from app.db.database import async_session_maker
from app.services.redis_client import close_redis
from app.routers import api_router
from app.services.quiz_reminder import QuizReminderService

from loguru import logger

logger.add("log/meduzzen.log")
logger.debug("That's it, beautiful and simple logging!")

scheduler = AsyncIOScheduler(timezone=timezone.utc)
reminder_service = QuizReminderService()


async def run_reminders_job() -> None:
    async with async_session_maker() as db:
        now = datetime.now(timezone.utc)
        await reminder_service.run_daily_reminders(db, now_utc=now)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await close_redis()
    scheduler.add_job(
        run_reminders_job,
        trigger=CronTrigger(hour=0, minute=0),
        id="quiz_daily_reminders",
        replace_existing=True,
    )

    scheduler.start()

    try:
        yield
    finally:
        scheduler.shutdown(wait=False)


app = FastAPI()
register_exception_handlers(app)
app.include_router(api_router)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.app.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(NotFound)
async def not_found_handler(request: Request, exc: NotFound):
    return JSONResponse(
        status_code=404,
        content={"detail": str(exc) or "Not found"}
    )


@app.exception_handler(Conflict)
async def conflict_handler(request: Request, exc: Conflict):
    return JSONResponse(
        status_code=409,
        content={"detail": str(exc) or "Conflict"}
    )

if __name__ == "__main__":
    import uvicorn
    from app.core.config import settings

    uvicorn.run(
        "app.main:app",
        host=settings.app.HOST,
        port=settings.app.PORT,
        reload=settings.app.RELOAD,
    )
