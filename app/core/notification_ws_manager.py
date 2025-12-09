from __future__ import annotations

from typing import Dict, List
from fastapi import WebSocket


class NotificationWebSocketManager:

    def __init__(self) -> None:
        self._connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, user_id: int, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.setdefault(user_id, []).append(websocket)

    async def disconnect(self, user_id: int, websocket: WebSocket) -> None:
        user_conns = self._connections.get(user_id)
        if not user_conns:
            return

        if websocket in user_conns:
            user_conns.remove(websocket)

        if not user_conns:
            self._connections.pop(user_id, None)

    async def send_to_user(self, user_id: int, message: dict) -> None:

        user_conns = self._connections.get(user_id)
        if not user_conns:
            return

        living_conns: list[WebSocket] = []
        for ws in user_conns:
            try:
                await ws.send_json(message)
                living_conns.append(ws)
            except Exception:
                pass

        if living_conns:
            self._connections[user_id] = living_conns
        else:
            self._connections.pop(user_id, None)


notifications_ws_manager = NotificationWebSocketManager()
