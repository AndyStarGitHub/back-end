from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.quiz_reminder import QuizReminderService

from app.db.database import async_session_maker


async def run_reminders_once() -> None:

    service = QuizReminderService()

    async with async_session_maker() as db:  # type: AsyncSession

        now = datetime.now(timezone.utc)
        await service.run_daily_reminders(db, now_utc=now)


def main() -> None:

    asyncio.run(run_reminders_once())


if __name__ == "__main__":
    main()
