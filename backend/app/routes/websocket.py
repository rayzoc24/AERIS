"""WebSocket router for real-time updates (vehicle position, signal states).

We accept an access token passed either as a query parameter or as a
cookie. The query approach is the only way for browser WebSocket
clients because they cannot set Authorization headers.
"""
import logging
from typing import Dict, Set

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect, status

from app.security.jwt import decode_token, TokenType

logger = logging.getLogger("aeris.ws")
router = APIRouter(tags=["ws"])


class ConnectionManager:
    def __init__(self) -> None:
        # trip_id -> set of websocket connections subscribed to that trip
        self._channels: Dict[str, Set[WebSocket]] = {}

    async def connect(self, trip_id: str, ws: WebSocket) -> None:
        await ws.accept()
        self._channels.setdefault(trip_id, set()).add(ws)
        logger.info("WS connected to trip %s, total=%d", trip_id, len(self._channels[trip_id]))

    def disconnect(self, trip_id: str, ws: WebSocket) -> None:
        if trip_id in self._channels:
            self._channels[trip_id].discard(ws)
            if not self._channels[trip_id]:
                self._channels.pop(trip_id, None)

    async def broadcast(self, trip_id: str, message: dict) -> None:
        for ws in list(self._channels.get(trip_id, [])):
            try:
                await ws.send_json(message)
            except Exception:
                self.disconnect(trip_id, ws)


manager = ConnectionManager()


@router.websocket("/ws/trips/{trip_id}")
async def trip_socket(
    websocket: WebSocket,
    trip_id: str,
    token: str = Query(...),
):
    try:
        payload = decode_token(token, expected_type=TokenType.ACCESS)
    except Exception:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    await manager.connect(trip_id, websocket)
    try:
        while True:
            data = await websocket.receive_json()
            # Echo only admin/driver messages to all subscribers; citizens are read-only.
            if payload.get("role") in {"admin", "driver"} and data.get("type") in {"position", "status"}:
                await manager.broadcast(trip_id, data)
    except WebSocketDisconnect:
        manager.disconnect(trip_id, websocket)
