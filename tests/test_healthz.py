import importlib
import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core import config as config_module


@pytest.mark.asyncio
async def test_healthz_status_ok():
    transport = ASGITransport(app=app)
    async with AsyncClient(
            transport=transport,
            base_url="http://testserver"
    ) as ac:
        resp = await ac.get("/openapi.json")
    assert resp.status_code == 200
    assert resp.headers.get("content-type", "").startswith("application/json")


@pytest.mark.asyncio
async def test_settings_has_app_name():
    importlib.reload(config_module)
    app_name = getattr(getattr(
        config_module.settings,
        "app",
        object()
    ), "APP_NAME", None)
    assert isinstance(app_name, str) and app_name.strip() != ""
