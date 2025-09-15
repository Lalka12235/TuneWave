from fastapi import (
    WebSocket,
    WebSocketDisconnect,
    Depends,
    Path,
    APIRouter,
    HTTPException,
    status,
    Query
)
from sqlalchemy.orm import Session
import uuid
from app.config.session import get_db
from app.auth.auth import get_current_user
from typing import Annotated
from app.models import User
from app.schemas.message_schemas import MessageCreate
from app.services.chat_service import ChatService
from app.ws.connection_manager import manager
import json
from app.services.user_service import UserService

chat_ws = APIRouter(
    tags=['Chat WS'],
    prefix='/ws/chat'
)

db_dependencies = Annotated[Session,Depends(get_db)]
user_dependencies = Annotated[User,Depends(get_current_user)]


async def get_websocket_user(db: db_dependencies, token: Annotated[str, Query(...,)]):
    user = UserService.get_user_by_token(db, token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный токен аутентификации"
        )
    return user


@chat_ws.websocket('/{room_id}')
async def send_message(
    websocket: WebSocket,
    room_id: Annotated[uuid.UUID, Path(..., description='Уникальный ID комнаты')],
    db: db_dependencies,
    user: Annotated[User, Depends(get_websocket_user)] 
):
    """
    Эндпоинт WebSocket для чата в комнате.
    """
    await manager.connect(room_id, websocket)

    try:
        while True:
            # Получаем JSON-строку от клиента
            data = await websocket.receive_text()
            
            try:
                # Парсим JSON
                message_data = json.loads(data)
                text = message_data['text']
            except (json.JSONDecodeError, KeyError):
                # Если формат сообщения неверный, пропускаем
                continue

            # Используем user.id, полученный при аутентификации
            new_message = ChatService.create_message(
                db, room_id, user.id, MessageCreate(text=text)
            )
            
            # Преобразуем объект сообщения в JSON-строку
            new_message_json = new_message.model_dump_json()
            
            # Рассылаем всем в комнате
            await manager.broadcast(room_id, new_message_json)
    
    except WebSocketDisconnect:
        # Теперь у нас есть user.id из аутентификации
        manager.disconnect(room_id, websocket)
        await manager.broadcast(room_id, f'Пользователь {user.username} ушел')