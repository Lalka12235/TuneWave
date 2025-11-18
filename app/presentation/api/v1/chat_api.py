import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query
from fastapi_limiter.depends import RateLimiter

from app.domain.entity import UserEntity
from app.presentation.schemas.message_schemas import MessageCreate, MessageResponse
from app.application.services.chat_service import ChatService

from dishka import FromDishka

chat = APIRouter(
    tags=['Chat'],
    prefix='/chat'
)

user_dependencies = FromDishka[UserEntity]
chat_service = FromDishka[ChatService]


@chat.get('/{room_id}',response_model=list[MessageResponse],dependencies=[Depends(RateLimiter(times=10, seconds=60))])
async def get_message_for_room(
    chat_service: chat_service,
    room_id: Annotated[uuid.UUID,Path(...,description='Уникальный ID комнаты')],
    limit: Annotated[int,Query(...,description='Лимит на отображение сообщений в комнате')] = 10,
    before_timestamp: Annotated[datetime | None, Query(
        description='Метка времени последнего сообщения, для пагинации'
    )] = None,
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
        user (User): Текущий авторизованный пользователь.

    Returns:
        list[MessageResponse]: Список объектов сообщений.
    """
    return chat_service.get_message_for_room(room_id,limit,before_timestamp)


@chat.post('/{room_id}',response_model=MessageResponse, status_code=201,dependencies=[Depends(RateLimiter(times=5, seconds=5))])
async def create_message(
    chat_service: chat_service,
    room_id: Annotated[uuid.UUID,Path(...,description='Уникальный ID комнаты')],
    user: user_dependencies,
    message: MessageCreate,
) -> MessageResponse:
    """
    Создает новое сообщение в комнате.
    
    Пользователь должен быть участником комнаты. 
    Сообщение сохраняется в базе данных и возвращается клиенту.

    Args:
        room_id (uuid.UUID): Уникальный ID комнаты.
        user (User): Текущий авторизованный пользователь.
        message (MessageCreate): Pydantic-схема, содержащая текст сообщения.

    Returns:
        MessageResponse: Объект созданного сообщения с ID и временной меткой.
    """
    return chat_service.create_message(room_id,user.id,message)