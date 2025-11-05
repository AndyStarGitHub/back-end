import os
import tempfile
import pytest

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession
)
from sqlalchemy.pool import NullPool
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.db.database import Base, get_db


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture()
def test_db_url():
    explicit = os.getenv("TEST_ASYNC_DB_URL")
    if explicit:
        return explicit
    _, path = tempfile.mkstemp(suffix=".db")
    return f"sqlite+aiosqlite:///{path}"


@pytest.fixture()
async def engine(test_db_url: str):
    eng = create_async_engine(
        test_db_url,
        poolclass=NullPool,
        future=True
    )
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    try:
        yield eng
    finally:
        async with eng.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await eng.dispose()


@pytest.fixture()
async def db_session(engine):
    Session = async_sessionmaker(
        bind=engine,
        expire_on_commit=False,
        class_=AsyncSession
    )
    async with Session() as session:
        yield session


@pytest.fixture()
async def client(db_session: AsyncSession):
    async def override_get_db():
        yield db_session

    async def override_get_session():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_db] = override_get_session

    transport = ASGITransport(app=app)
    async with AsyncClient(
            transport=transport,
            base_url="http://testserver",
            follow_redirects=True
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def stub_password_hash(monkeypatch):
    def fake_hash(pw: str) -> str:
        return f"hashed::{pw}"

    import app.core.security as security
    import app.repositories.user_repo as user_repo

    monkeypatch.setattr(
        security,
        "hash_password",
        fake_hash,
        raising=True
    )
    monkeypatch.setattr(
        user_repo,
        "hash_password",
        fake_hash,
        raising=True
    )
