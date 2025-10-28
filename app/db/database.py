from app.core.config import db_settings
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession
)

engine = create_async_engine(
    db_settings.ASYNC_DATABASE_URL,   # <-- ось так правильно
    echo=False, pool_pre_ping=True
)

async_session = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession
)


async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session
