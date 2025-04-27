from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.config.ws_config import manager


ws = APIRouter(tags=['WebSocket'])


@ws.websocket('/ws/{room_name}/{username}')
async def enter_or_leave_room(websocket: WebSocket,room_name: str, username: str):
    await manager.connect(room_name,websocket)
    await manager.broadcast(room_name,f'{username} was joined the room')

    try: 
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(room_name,f'{username}: {data}')

    except WebSocketDisconnect:
        manager.disconnect(room_name,websocket)
        await manager.broadcast(room_name,f'{username} left this room')