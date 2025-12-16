import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import Conflict, NotFound, Forbidden
from app.schemas.user import UserCreate, UserUpdate
from app.services.user_service import UserService

pytestmark = pytest.mark.anyio


async def test_create_user_conflict_when_email_exists(
    db_session: AsyncSession,
    user_factory,
):
    await user_factory(email="taken@example.com")

    svc = UserService(db_session)
    payload = UserCreate(
        email="taken@example.com",
        password="password",
        full_name="X"
    )

    with pytest.raises(Conflict):
        await svc.create_user(payload)


async def test_get_user_not_found(db_session: AsyncSession):
    svc = UserService(db_session)
    with pytest.raises(NotFound):
        await svc.get_user(999999)


async def test_update_user_cannot_change_email(
    db_session: AsyncSession,
    user_factory,
):
    usf = await user_factory(email="u@example.com")
    svc = UserService(db_session)

    class PayloadWithEmail:
        def model_dump(self, **kwargs):
            return {"email": "new@example.com"}

    with pytest.raises(Conflict):
        await svc.update_user(usf.id, PayloadWithEmail())


async def test_update_user_with_only_password_returns_user_unchanged(
    db_session: AsyncSession,
    user_factory,
):
    usf = await user_factory(
        email="u@example.com",
        hashed_password="hashed::old"
    )
    svc = UserService(db_session)

    payload = UserUpdate(password="newpass")
    res = await svc.update_user(usf.id, payload)

    assert res.id == usf.id
    assert res.email == usf.email
    assert res.hashed_password == "hashed::old"


async def test_update_user_updates_profile_fields(
    db_session: AsyncSession,
    user_factory,
):
    usf = await user_factory(email="u@example.com", full_name="Old Name")
    svc = UserService(db_session)

    payload = UserUpdate(full_name="New Name", about="About", phone="123")
    res = await svc.update_user(usf.id, payload)

    assert res.id == usf.id
    assert res.full_name == "New Name"
    assert res.about == "About"
    assert res.phone == "123"


async def test_change_password_wrong_old_password_forbidden(
    db_session: AsyncSession,
    user_factory,
):
    usf = await user_factory(
        email="u@example.com",
        hashed_password="hashed::old"
    )
    svc = UserService(db_session)

    with pytest.raises(Forbidden):
        await svc.change_password(
            current_user=usf,
            old_password="WRONG",
            new_password="new",
        )


async def test_change_password_success(
    db_session: AsyncSession,
    user_factory,
):
    usf = await user_factory(
        email="u@example.com",
        hashed_password="hashed::old"
    )
    svc = UserService(db_session)

    res = await svc.change_password(
        current_user=usf,
        old_password="old",
        new_password="new",
    )

    assert res.hashed_password == "hashed::new"
