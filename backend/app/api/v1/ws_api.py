from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.ws.connection_manager import manager
import uuid

ws = APIRouter(
    tags=['WebSockets'],
    prefix='/ws'
)

@ws.websocket("/room/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: uuid.UUID):
    await manager.connect(room_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(room_id, websocket)