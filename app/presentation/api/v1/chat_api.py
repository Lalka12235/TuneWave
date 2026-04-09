import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter,Path, Query

from app.domain.entity import UserEntity,MessageEntity
from app.presentation.schemas.message_schemas import MessageCreate, MessageResponse
from app.application.commands.chat import MessageCreate,ReadMessage

from dishka.integrations.fastapi import DishkaRoute,FromDishka


chat = APIRouter(
    tags=['Chat'],
    prefix='/chat',
    route_class=DishkaRoute
)

def convert_entity_to_schema(entity: MessageEntity) -> MessageResponse:
    return MessageResponse(
        id=entity.id,
        text=entity.text,
        user_id=entity.user_id,
        room_id=entity.room_id,
        created_at=entity.created_at
    )


@chat.get('/{room_id}',response_model=list[MessageResponse])
async def get_message_for_room(
    interactor: FromDishka[ReadMessage],
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
    """
    result = interactor.get_message_for_room(room_id,limit,before_timestamp)
    return [convert_entity_to_schema(res) for res in result]


@chat.post('/{room_id}',response_model=MessageResponse, status_code=201)
async def create_message(
    interactor: FromDishka[MessageCreate],
    room_id: Annotated[uuid.UUID,Path(...,description='Уникальный ID комнаты')],
    user: FromDishka[UserEntity],
    message: MessageCreate,
) -> MessageResponse:
    """
    Создает новое сообщение в комнате.
    
    Пользователь должен быть участником комнаты. 
    Сообщение сохраняется в базе данных и возвращается клиенту.
    """
    result = interactor.create_message(room_id,user.id,message.text)
    return [convert_entity_to_schema(res) for res in result] 