from fastapi import APIRouter,Depends,Path,Query
from sqlalchemy.orm import Session
import uuid
from app.config.session import get_db
from app.auth.auth import get_current_user
from typing import Annotated
from app.models.user import User
from app.schemas.message_schemas import MessageResponse, MessageCreate
from app.services.chat_service import ChatService
from datetime import datetime
from fastapi_limiter.depends import RateLimiter


chat = APIRouter(
    tags=['Chat'],
    prefix='/chat'
)

db_dependencies = Annotated[Session,Depends(get_db)]
user_dependencies = Annotated[User,Depends(get_current_user)]


@chat.get('/{room_id}',response_model=list[MessageResponse])
async def get_message_for_room(
    room_id: Annotated[uuid.UUID,Path(...,description='Уникальный ID комнаты')],
    user: user_dependencies,
    db: db_dependencies,
    limit: Annotated[int,Query(...,description='Лимит на отображение сообщений в комнате')],
    before_timestamp: Annotated[datetime | None, Query(
        description='Метка времени последнего сообщения, для пагинации'
    )] = None,
    dependencies=[Depends(RateLimiter(times=10, seconds=60))],
) -> list[MessageResponse]:
    """
    Получает историю сообщений для указанной комнаты.
    
    Эта функция позволяет получить до 50 последних сообщений в комнате.
    Для пагинации можно передать `before_timestamp` — временную метку
    последнего сообщения, чтобы получить более старые сообщения.

    Args:
        room_id (uuid.UUID): Уникальный ID комнаты.
        before_timestamp (datetime, optional): Временная метка для пагинации.
        limit (int, optional): Максимальное количество сообщений для возврата.
        db (Session): Сессия базы данных.
        user (User): Текущий авторизованный пользователь.

    Returns:
        list[MessageResponse]: Список объектов сообщений.
    """
    return ChatService.get_message_for_room(db,room_id,limit,before_timestamp)


@chat.post('/{room_id}',response_model=MessageResponse, status_code=201)
async def create_message(
    room_id: Annotated[uuid.UUID,Path(...,description='Уникальный ID комнаты')],
    db: db_dependencies,
    user: user_dependencies,
    message: MessageCreate,
    dependencies=[Depends(RateLimiter(times=5, seconds=5))]
) -> MessageResponse:
    """
    Создает новое сообщение в комнате.
    
    Пользователь должен быть участником комнаты. 
    Сообщение сохраняется в базе данных и возвращается клиенту.

    Args:
        room_id (uuid.UUID): Уникальный ID комнаты.
        db (Session): Сессия базы данных.
        user (User): Текущий авторизованный пользователь.
        message (MessageCreate): Pydantic-схема, содержащая текст сообщения.

    Returns:
        MessageResponse: Объект созданного сообщения с ID и временной меткой.
    """
    return ChatService.create_message(db,room_id,user.id,message)