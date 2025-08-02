from fastapi import WebSocket
import uuid


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[uuid.UUID,list[WebSocket]] = {}


    async def connect(self,room_id: uuid.UUID,websocket: WebSocket):
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
        self.active_connections[room_id].append(websocket)

    
    def disconnect(self,room_id: uuid.UUID,websocket: WebSocket):
        if room_id in self.active_connections:
            self.active_connections[room_id].remove(websocket)
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]

    
    async def broadcast(self, room_id: uuid.UUID, message: str):
        """
        Отправляет сообщение всем клиентам в определённой комнате.
        """
        if room_id in self.active_connections:
            for connection in self.active_connections[room_id]:
                await connection.send_text(message)


manager = ConnectionManager()