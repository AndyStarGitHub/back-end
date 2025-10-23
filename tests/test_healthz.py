import importlib
import os
from typing import Any

import pytest
from httpx import AsyncClient, ASGITransport
from fastapi import status

from app.main import app
from app.core import config as config_module


@pytest.mark.asyncio
async def test_healthz_status_and_payload():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/")

    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()

    assert isinstance(data, dict)
    assert data.get("result") == "working"
    assert data.get("detail") == "ok"
    assert data.get("status_code") == 200


@pytest.mark.asyncio
async def test_settings_reads_app_name_from_env(monkeypatch: Any) -> None:

    old = os.environ.get("APP_NAME")

    test_value = "My Test App From ENV"
    monkeypatch.setenv("APP_NAME", test_value)

    importlib.reload(config_module)

    assert config_module.settings.APP_NAME == test_value

    if old is not None:
        monkeypatch.setenv("APP_NAME", old)
    else:
        monkeypatch.delenv("APP_NAME", raising=False)

    importlib.reload(config_module)
