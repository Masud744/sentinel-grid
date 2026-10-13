import asyncio
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.websocket.manager import ws_manager

logger = logging.getLogger("scs_rg.websocket")
router = APIRouter(tags=["WebSocket Real-Time Feed"])


@router.websocket("/ws/updates")
async def websocket_updates_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        # Send initial confirmation message
        await websocket.send_json({
            "event": "CONNECTED",
            "data": {"status": "ONLINE", "message": "SCS-RG Grid Live Telemetry Feed Connected"}
        })

        while True:
            # Keep connection alive while listening for client messages/pings
            try:
                data = await websocket.receive_text()
                if data == "ping":
                    await websocket.send_text("pong")
            except asyncio.CancelledError:
                break
    except WebSocketDisconnect:
        logger.info("[WS SERVER] Client initiated WebSocket disconnect.")
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"[WS SERVER] Unexpected WebSocket exception: {e}")
        ws_manager.disconnect(websocket)
