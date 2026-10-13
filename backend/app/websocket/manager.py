"""
FastAPI Native WebSocket Connection Manager.

Manages active WebSocket dashboard connections and broadcasts real-time
event streams (zone state changes, priority queue updates, alerts).
"""

import json
import logging
from typing import List, Dict, Any
from fastapi import WebSocket

logger = logging.getLogger("scs_rg.websocket")
logging.basicConfig(level=logging.INFO)


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        client_host = websocket.client.host if websocket.client else "unknown"
        logger.info(f"[WS SERVER] Client connected from {client_host}. Total active connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            client_host = websocket.client.host if websocket.client else "unknown"
            logger.info(f"[WS SERVER] Client disconnected from {client_host}. Total active connections: {len(self.active_connections)}")

    async def broadcast(self, event_type: str, payload: Dict[str, Any]):
        message = {
            "event": event_type,
            "data": payload
        }
        json_msg = json.dumps(message, default=str)
        
        if not self.active_connections:
            logger.debug(f"[WS SERVER] Broadcast '{event_type}' called but no active WS clients connected.")
            return

        logger.info(f"[WS SERVER] Broadcasting '{event_type}' to {len(self.active_connections)} client(s)...")

        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(json_msg)
            except Exception as e:
                logger.warning(f"[WS SERVER] Error sending message to client: {e}")
                disconnected.append(connection)

        for conn in disconnected:
            self.disconnect(conn)


ws_manager = ConnectionManager()
