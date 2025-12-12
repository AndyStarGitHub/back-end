import os
import tempfile
import pytest

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession
)
from sqlalchemy.pool import NullPool
from fastapi import HTTPException
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.db.database import Base, get_db


from typing import Callable

from app.models.user import User
from app.models.company import Company, CompanyVisibilityEnum
from app.models.company_member import CompanyMember, CompanyMemberRoleEnum

from app.core.deps import get_current_user


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

    app.dependency_overrides[get_db] = override_get_db

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
    monkeypatch.setattr(security, "hash_password", fake_hash, raising=True)

    try:
        import app.services.user_service as user_service
        monkeypatch.setattr(
            user_service,
            "hash_password",
            fake_hash,
            raising=False
        )
    except Exception:
        pass

    try:
        import app.repositories.user_repo as user_repo
        if hasattr(user_repo, "hash_password"):
            monkeypatch.setattr(
                user_repo,
                "hash_password",
                fake_hash,
                raising=True
            )
    except Exception:
        pass


@pytest.fixture()
async def user_factory(db_session: AsyncSession) -> Callable[..., User]:
    async def _create_user(
        email: str = "user@example.com",
        hashed_password: str = "hashed::test",
        is_active: bool = True,
        **extra,
    ) -> User:
        user = User(
            email=email,
            hashed_password=hashed_password,
            is_active=is_active,
            **extra,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user

    return _create_user


@pytest.fixture()
async def company_factory(
    db_session: AsyncSession,
    user_factory: Callable[..., User],
) -> Callable[..., Company]:
    async def _create_company(
        owner: User | None = None,
        name: str = "Test Company",
        description: str = "Test description",
        visibility: str = CompanyVisibilityEnum.PUBLIC.value,
    ) -> Company:
        if owner is None:
            owner = await user_factory()

        company = Company(
            name=name,
            description=description,
            visibility=visibility,
            owner_id=owner.id,
        )
        db_session.add(company)
        await db_session.commit()
        await db_session.refresh(company)
        return company

    return _create_company


@pytest.fixture()
async def company_member_factory(
    db_session: AsyncSession,
) -> Callable[..., "CompanyMember"]:
    async def _create_company_member(
        company: Company,
        user: User,
        role: CompanyMemberRoleEnum = CompanyMemberRoleEnum.MEMBER,
    ) -> CompanyMember:
        member = CompanyMember(
            company_id=company.id,
            user_id=user.id,
            role=role,
        )
        db_session.add(member)
        await db_session.commit()
        await db_session.refresh(member)
        return member

    return _create_company_member


@pytest.fixture()
def override_current_user():
    def _apply(user: User | None):
        if user is None:
            async def _unauthorized():
                raise HTTPException(
                    status_code=401,
                    detail="Not authenticated"
                )
            app.dependency_overrides[get_current_user] = _unauthorized
        else:
            async def _authorized():
                return user
            app.dependency_overrides[get_current_user] = _authorized

    yield _apply

    app.dependency_overrides.pop(get_current_user, None)

