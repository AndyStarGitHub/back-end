from fastapi import FastAPI
from fastapi.testclient import TestClient

import app.api.notifications_ws as notifications_ws


ws_app = FastAPI()
ws_app.include_router(notifications_ws.router)

client = TestClient(ws_app)


def test_websocket_notifications_success(monkeypatch):

    class DummyUser:
        def __init__(self, user_id: int) -> None:
            self.id = user_id

    async def fake_get_db():
        yield object()

    async def fake_get_user_from_token(db, token: str):
        assert token == "valid-token"
        return DummyUser(user_id=123)

    calls = {"connect": [], "disconnect": []}

    class DummyManager:
        async def connect(self, user_id, websocket):
            calls["connect"].append(user_id)
            await websocket.accept()

        async def disconnect(self, user_id, websocket):
            calls["disconnect"].append(user_id)

    monkeypatch.setattr(notifications_ws, "get_db", fake_get_db)
    monkeypatch.setattr(
        notifications_ws,
        "get_user_from_token",
        fake_get_user_from_token
    )
    monkeypatch.setattr(
        notifications_ws,
        "notifications_ws_manager",
        DummyManager()
    )

    with client.websocket_connect("/ws/notifications?token=valid-token") as ws:
        ws.send_text("ping")

    assert calls["connect"] == [123]
    assert calls["disconnect"] == [123]
