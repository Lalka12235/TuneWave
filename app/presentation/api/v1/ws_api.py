import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.infrastracture.ws.connection_manager import manager

ws = APIRouter(
    tags=['WebSockets'],
    prefix='/ws'
)


@ws.websocket("/room/{room_id}/{user_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: uuid.UUID,user_id: uuid.UUID):
    await manager.connect(manager.GLOBAL_ROOM_ID,websocket)
    await manager.connect(room_id,user_id, websocket)
    if room_id != manager.GLOBAL_ROOM_ID: 
        await manager.connect(room_id, user_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(manager.GLOBAL_ROOM_ID, user_id, websocket)
        if room_id != manager.GLOBAL_ROOM_ID:
            manager.disconnect(room_id, user_id, websocket)
    except Exception:
        manager.disconnect(manager.GLOBAL_ROOM_ID, user_id, websocket)
        if room_id != manager.GLOBAL_ROOM_ID:
            manager.disconnect(room_id, user_id, websocket)