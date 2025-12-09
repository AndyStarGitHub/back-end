from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.notification_ws_manager import notifications_ws_manager
from app.core.deps import get_user_from_token
from app.db.database import get_db

router = APIRouter()


@router.websocket("/ws/notifications")
async def websocket_notifications(
    websocket: WebSocket,
    db: AsyncSession = Depends(get_db),
):

    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    try:
        user = await get_user_from_token(db, token)
    except Exception:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    user_id = user.id

    await notifications_ws_manager.connect(user_id, websocket)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await notifications_ws_manager.disconnect(user_id, websocket)
