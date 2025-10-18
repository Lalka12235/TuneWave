from fastapi import WebSocket
import uuid




class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[uuid.UUID,list[WebSocket]] = {}
        self.user_connections: dict[uuid.UUID,WebSocket] =  {}

    GLOBAL_ROOM_ID = uuid.UUID('00000000-0000-0000-0000-000000000000')


    async def connect(self,room_id: uuid.UUID,user_id: uuid.UUID,websocket: WebSocket):
        """
        Устанавливает новое WebSocket-соединение и привязывает его к комнате и пользователю.
        """
        await websocket.accept()
        self.user_connections[user_id] = websocket
        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
        self.active_connections[room_id].append(websocket)
        

    
    def disconnect(self,room_id: uuid.UUID,user_id: uuid.UUID,websocket: WebSocket):
        """
        Разрывает WebSocket-соединение и удаляет его из списков.
        """
        if user_id in self.user_connections: 
            del self.user_connections[user_id]
        if room_id in self.active_connections:
            self.active_connections[room_id].remove(websocket)
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]

    
    async def broadcast(self, room_id: uuid.UUID, message: str):
        """
        Отправляет сообщение всем клиентам в определённой комнате.
        Сообщение должно быть в формате JSON-строки.
        """
        if room_id in self.active_connections:
            for connection in self.active_connections[room_id]:
                await connection.send_text(message)

    async def send_personal_message(self,message: str,user_id: uuid.UUID):
        """
        Отправляет персональное сообщение конкретному пользователю по его ID.
        Сообщение должно быть в формате JSON-строки.
        """
        if user_id in self.user_connections:
            websocket = self.user_connections[user_id]
            await websocket.send_text(message)