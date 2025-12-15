from __future__ import annotations
from datetime import datetime, timezone
import uuid

import pytest
from fastapi import HTTPException

from app.services.company import CompanyService
from app.schemas.company import (
    CompanyCreate,
    CompanyUpdate,
    CompanyRead,
    CompanyListResponse,
    CompanyVisibility,
)


class DummyUser:
    def __init__(self, id: int) -> None:
        self.id = id


class FakeCompany:
    def __init__(self, **kwargs) -> None:
        for k, v in kwargs.items():
            setattr(self, k, v)


class FakeCompanyRepository:
    def __init__(self) -> None:
        self._store: dict[uuid.UUID, FakeCompany] = {}

    async def create_one(self, db, **values):
        obj_id = uuid.uuid4()
        values.setdefault("id", obj_id)
        values.setdefault("created_at", datetime.now(timezone.utc))
        values.setdefault("updated_at", datetime.now(timezone.utc))
        obj = FakeCompany(**values)
        self._store[obj_id] = obj
        return obj

    async def get_by_id(self, db, obj_id):
        return self._store.get(obj_id)

    async def update_one(self, db, obj_id, **values):
        obj = self._store.get(obj_id)
        if obj is None:
            return None
        for ki, valu in values.items():
            setattr(obj, ki, valu)
        setattr(obj, "updated_at", datetime.now(timezone.utc))
        return obj

    async def delete_one(self, db, obj_id):
        return self._store.pop(obj_id, None) is not None

    async def get_public_paginated(
            self,
            db,
            *,
            offset: int = 0,
            limit: int = 50
    ):
        items = [c for c in self._store.values() if c.visibility == "public"]
        total = len(items)
        slice_items = items[offset : offset + limit]
        return total, slice_items

    async def get_by_owner_paginated(
        self,
        db,
        owner_id: int,
        *,
        offset: int = 0,
        limit: int = 50,
    ):
        items = [c for c in self._store.values() if c.owner_id == owner_id]
        total = len(items)
        slice_items = items[offset : offset + limit]
        return total, slice_items


@pytest.fixture
def service() -> CompanyService:
    repo = FakeCompanyRepository()
    return CompanyService(repo=repo)


@pytest.mark.anyio
async def test_create_company_sets_owner_and_hidden(service: CompanyService):
    user = DummyUser(id=1)
    data = CompanyCreate(name="My Company", description="Test company")

    result: CompanyRead = await service.create_company(
        db=None,
        current_user=user,
        data=data,
    )

    assert result.name == "My Company"
    assert result.description == "Test company"
    assert result.owner_id == 1
    assert result.visibility == CompanyVisibility.hidden


@pytest.mark.anyio
async def test_owner_can_see_hidden_company(service: CompanyService):
    owner = DummyUser(id=1)
    data = CompanyCreate(name="Hidden Co", description=None)

    created = await service.create_company(
        db=None,
        current_user=owner,
        data=data,
    )

    loaded = await service.get_company(
        db=None,
        company_id=created.id,
        current_user=owner,
    )

    assert loaded.id == created.id
    assert loaded.visibility == CompanyVisibility.hidden


@pytest.mark.anyio
async def test_non_owner_cannot_see_hidden_company(service: CompanyService):
    owner = DummyUser(id=1)
    other = DummyUser(id=2)

    created = await service.create_company(
        db=None,
        current_user=owner,
        data=CompanyCreate(name="Secret Co", description=None),
    )

    with pytest.raises(HTTPException) as exc_info:
        await service.get_company(
            db=None,
            company_id=created.id,
            current_user=other,
        )

    assert exc_info.value.status_code == 404


@pytest.mark.anyio
async def test_list_public_companies_returns_only_public(
        service: CompanyService
):
    user = DummyUser(id=1)

    hidden = await service.create_company(
        db=None,
        current_user=user,
        data=CompanyCreate(name="Hidden Co", description=None),
    )
    public = await service.create_company(
        db=None,
        current_user=user,
        data=CompanyCreate(name="Public Co", description=None),
    )
    await service.update_company(
        db=None,
        company_id=public.id,
        current_user=user,
        data=CompanyUpdate(visibility=CompanyVisibility.public),
    )

    resp: CompanyListResponse = await service.list_public_companies(
        db=None,
        offset=0,
        limit=10,
    )

    names = [c.name for c in resp.items]
    assert "Public Co" in names
    assert "Hidden Co" not in names


@pytest.mark.anyio
async def test_list_my_companies_returns_only_user_companies(
        service: CompanyService
):
    user1 = DummyUser(id=1)
    user2 = DummyUser(id=2)

    await service.create_company(
        db=None,
        current_user=user1,
        data=CompanyCreate(name="User1 Co1", description=None),
    )
    await service.create_company(
        db=None,
        current_user=user1,
        data=CompanyCreate(name="User1 Co2", description=None),
    )
    await service.create_company(
        db=None,
        current_user=user2,
        data=CompanyCreate(name="User2 Co1", description=None),
    )

    resp1: CompanyListResponse = await service.list_my_companies(
        db=None,
        current_user=user1,
        offset=0,
        limit=10,
    )
    resp2: CompanyListResponse = await service.list_my_companies(
        db=None,
        current_user=user2,
        offset=0,
        limit=10,
    )

    names1 = sorted(c.name for c in resp1.items)
    names2 = sorted(c.name for c in resp2.items)

    assert names1 == ["User1 Co1", "User1 Co2"]
    assert names2 == ["User2 Co1"]
