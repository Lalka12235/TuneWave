from fastapi import WebSocket
import uuid
from app.application.services.redis_service import RedisService


class ConnectionManager:
    def __init__(self,redis_serive: RedisService):
        self.redis_service = redis_serive

    GLOBAL_ROOM_ID = uuid.UUID('00000000-0000-0000-0000-000000000000')
    # global room id -> user_id | user_id -> websocket


    async def connect(self,room_id: uuid.UUID,user_id: uuid.UUID,websocket: WebSocket):
        """
        Устанавливает новое WebSocket-соединение и привязывает его к комнате и пользователю.
        """
        await websocket.accept()

        key = f'user_connection:{user_id}'
        await self.redis_service.set(key,websocket)
        if room_id not in self.active_connections:
            await self.redis_service.rpush(f'{room_id}', websocket)
            return
        

    async def disconnect(self,room_id: uuid.UUID,user_id: uuid.UUID,websocket: WebSocket):
        """
        Разрывает WebSocket-соединение
        """
        key_user_connection = f'user_connection:{user_id}'
        key_room_connection = str(room_id)

        exist_user_connection =await  self.redis_service.get(key_user_connection)
        if exist_user_connection:
            await self.redis_service.default_delete(key_user_connection)

        room_connections = await self.redis_service.lrange(str(key_room_connection))
        if room_connections:
            if websocket in room_connections:
                await self.redis_service.lrem(key_room_connection,websocket)

        room_connections = self.redis_service.lrange(str(key_room_connection))
        if not room_connections:
            await self.redis_service.default_delete(key_room_connection)
    
    async def broadcast(self, room_id: uuid.UUID, message: str):
        """
        Отправляет сообщение всем клиентам в определённой комнате.
        Сообщение должно быть в формате JSON-строки.
        """
        key_room_connection = str(room_id)

        room_connections = await self.redis_service.lrange(str(key_room_connection))

        if not room_connections:
            return

        connection: WebSocket

        if room_id in room_connections:
            for connection in room_connections:
                await connection.send_text(message)

    async def send_personal_message(self,message: str,user_id: uuid.UUID):
        """
        Отправляет персональное сообщение конкретному пользователю по его ID.
        Сообщение должно быть в формате JSON-строки.
        """
        key_user_connection = f'user_connection:{user_id}'

        exist_user_connection = await self.redis_service.get(key_user_connection)

        if exist_user_connection:
            websocket = exist_user_connection
            await websocket.send_text(message)

manager = ConnectionManager()