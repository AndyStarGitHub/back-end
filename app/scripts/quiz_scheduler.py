from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.services.quiz_reminder import QuizReminderService
from app.db.database import async_session_maker


async def run_reminders_job() -> None:

    service = QuizReminderService()

    async with async_session_maker() as db:
        now = datetime.now(timezone.utc)
        await service.run_daily_reminders(db, now_utc=now)


def main() -> None:

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    scheduler = AsyncIOScheduler(timezone=timezone.utc, event_loop=loop)

    scheduler.add_job(
        run_reminders_job,
        trigger=CronTrigger(hour=0, minute=0),
        id="quiz_daily_reminders",
        replace_existing=True,
    )

    scheduler.start()

    try:
        loop.run_forever()
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        scheduler.shutdown(wait=False)
        loop.stop()
        loop.close()


if __name__ == "__main__":
    main()
