from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine
)
from typing import AsyncIterator
from app.core.config import settings


engine = create_async_engine(
    settings.ASYNC_DATABASE_URL,
    echo=False,
    pool_pre_ping=True
)

SessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession
)


async def get_db() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        yield session
