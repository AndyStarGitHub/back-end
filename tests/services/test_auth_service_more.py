import pytest
import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import InvalidCredentials, InactiveUser, TokenDecodeError
from app.services.auth_service import AuthService

pytestmark = pytest.mark.anyio


@pytest.fixture()
def auth_settings(monkeypatch):
    import app.services.auth_service as auth_mod

    class Sec:
        JWT_SECRET = "access-secret"
        JWT_ALG = "HS256"
        JWT_EXPIRES_MIN = 15

        JWT_REFRESH_SECRET = "refresh-secret"
        JWT_REFRESH_ALG = "HS256"
        JWT_REFRESH_EXPIRES_MIN = 60

    monkeypatch.setattr(auth_mod.settings, "security", Sec(), raising=False)
    return auth_mod


async def test_login_with_password_success(
    db_session: AsyncSession,
    user_factory,
    monkeypatch,
    auth_settings,
):
    import app.services.auth_service as auth_mod

    user = await user_factory(
        email="u@example.com",
        hashed_password="hashed::pw",
        is_active=True
    )

    monkeypatch.setattr(
        auth_mod,
        "verify_password",
        lambda pw, hpw: True,
        raising=True
    )

    svc = AuthService(db_session)
    tokens = await svc.login_with_password(email=user.email, password="pw")

    assert "access_token" in tokens
    assert tokens["token_type"] == "bearer"


async def test_login_with_password_inactive_user(
    db_session: AsyncSession,
    user_factory,
    monkeypatch,
    auth_settings,
):
    import app.services.auth_service as auth_mod

    user = await user_factory(
        email="u@example.com",
        hashed_password="hashed::pw",
        is_active=False
    )
    monkeypatch.setattr(
        auth_mod,
        "verify_password",
        lambda pw, hpw: True,
        raising=True
    )

    svc = AuthService(db_session)
    with pytest.raises(InactiveUser):
        await svc.login_with_password(email=user.email, password="pw")


async def test_refresh_access_token_invalid_token_raises_invalid_credentials(
    db_session: AsyncSession,
    auth_settings,
):
    svc = AuthService(db_session)
    with pytest.raises(InvalidCredentials):
        await svc.refresh_access_token("NOT_A_JWT")


async def test_refresh_access_token_wrong_type_raises_invalid_credentials(
    db_session: AsyncSession,
    auth_settings,
):
    import app.services.auth_service as auth_mod

    token = jwt.encode(
        {"type": "access", "sub": "1"},
        auth_mod.settings.security.JWT_REFRESH_SECRET,
        algorithm=auth_mod.settings.security.JWT_REFRESH_ALG,
    )

    svc = AuthService(db_session)
    with pytest.raises(InvalidCredentials):
        await svc.refresh_access_token(token)


async def test_refresh_access_token_missing_sub_raises_invalid_credentials(
    db_session: AsyncSession,
    auth_settings,
):
    import app.services.auth_service as auth_mod

    token = jwt.encode(
        {"type": "refresh"},
        auth_mod.settings.security.JWT_REFRESH_SECRET,
        algorithm=auth_mod.settings.security.JWT_REFRESH_ALG,
    )

    svc = AuthService(db_session)
    with pytest.raises(InvalidCredentials):
        await svc.refresh_access_token(token)


async def test_refresh_access_token_user_not_found_raises_invalid_credentials(
    db_session: AsyncSession,
    auth_settings,
    monkeypatch,
):
    import app.services.auth_service as auth_mod

    async def fake_get_by_id(db, user_id: int):
        return None

    monkeypatch.setattr(
        auth_mod.user_repo,
        "get_by_id",
        fake_get_by_id,
        raising=True)

    token = jwt.encode(
        {"type": "refresh", "sub": "999"},
        auth_mod.settings.security.JWT_REFRESH_SECRET,
        algorithm=auth_mod.settings.security.JWT_REFRESH_ALG,
    )

    svc = AuthService(db_session)
    with pytest.raises(InvalidCredentials):
        await svc.refresh_access_token(token)


async def test_decode_access_token_invalid_raises_token_decode_error(
        auth_settings
):
    import app.services.auth_service as auth_mod

    with pytest.raises(TokenDecodeError):
        auth_mod.decode_access_token("NOT_A_JWT")


async def test_decode_access_token_wrong_type_raises_token_decode_error(
        auth_settings
):
    import app.services.auth_service as auth_mod

    bad = jwt.encode(
        {"sub": "1", "type": "refresh"},
        auth_mod.settings.security.JWT_SECRET,
        algorithm=auth_mod.settings.security.JWT_ALG,
    )

    with pytest.raises(TokenDecodeError):
        auth_mod.decode_access_token(bad)
