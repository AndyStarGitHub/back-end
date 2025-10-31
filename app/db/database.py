from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine
)
from typing import AsyncIterator
from app.core.config import settings


ASYNC_DATABASE_URL = settings.db.ASYNC_DATABASE_URL

engine = create_async_engine(ASYNC_DATABASE_URL, echo=False, future=True)

SessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession
)


async def get_db() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        yield session
