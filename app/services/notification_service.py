"""
Tax God - WebSocket Notification Service
"""

from __future__ import annotations

import json
from collections import defaultdict

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = defaultdict(list)

    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[user_id].append(websocket)

    def disconnect(self, user_id: str, websocket: WebSocket):
        self.active_connections[user_id].remove(websocket)
        if not self.active_connections[user_id]:
            del self.active_connections[user_id]

    async def notify_user(self, user_id: str, event_type: str, payload: dict):
        message = json.dumps({"event_type": event_type, "payload": payload})
        for ws in self.active_connections.get(user_id, []):
            try:
                await ws.send_text(message)
            except Exception:
                pass

    async def broadcast(self, event_type: str, payload: dict):
        message = json.dumps({"event_type": event_type, "payload": payload})
        for connections in self.active_connections.values():
            for ws in connections:
                try:
                    await ws.send_text(message)
                except Exception:
                    pass


manager = ConnectionManager()
