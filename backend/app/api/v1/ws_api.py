from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.ws.connection_manager import manager,GLOBAL_ROOM_ID
import uuid

ws = APIRouter(
    tags=['WebSockets'],
    prefix='/ws'
)


@ws.websocket("/room/{room_id}/{user_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: uuid.UUID,user_id: uuid.UUID):
    await manager.connect(GLOBAL_ROOM_ID,websocket)
    await manager.connect(room_id,user_id, websocket)
    if room_id != GLOBAL_ROOM_ID: 
        await manager.connect(room_id, user_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(GLOBAL_ROOM_ID, user_id, websocket)
        if room_id != GLOBAL_ROOM_ID:
            manager.disconnect(room_id, user_id, websocket)
    except Exception:
        manager.disconnect(GLOBAL_ROOM_ID, user_id, websocket)
        if room_id != GLOBAL_ROOM_ID:
            manager.disconnect(room_id, user_id, websocket)