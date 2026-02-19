import uuid
from typing import Annotated

from fastapi import APIRouter, Cookie, Path, Query, status


from app.domain.entity import UserEntity
from app.presentation.schemas.room_schemas import (
    RoomCreate,
    RoomResponse,
    RoomUpdate,
)
from app.application.services.room_service import RoomService

from app.application.services.redis_service import RedisService

from dishka.integrations.fastapi import DishkaRoute,FromDishka,inject

room = APIRouter(tags=["Room"], prefix="/rooms",route_class=DishkaRoute)

user_dependencies = FromDishka[UserEntity]
redis_service = FromDishka[RedisService]
room_service = FromDishka[RoomService]


@room.post(
    "/",
    response_model=RoomResponse,
    status_code=status.HTTP_201_CREATED,
)
@inject
async def create_room(
    room_data: RoomCreate,
    current_user: user_dependencies,
    room_serv: room_service,
    session_id: Annotated[str | None, Cookie()] = None,
) -> RoomResponse:
    """
    Создает новую комнату.
    Требуется аутентификация. Владелец комнаты будет текущим аутентифицированным пользователем.
    """
    room_data = room_data.model_dump()
    current_user.set_session_id = session_id
    user_from_identity = current_user.get_current_user()
    return await room_serv.create_room(room_data, user_from_identity)


@room.put(
    "/{room_id}",
    response_model=RoomResponse,
)
@inject
def update_room(
    room_id: Annotated[uuid.UUID, Path(..., description="ID комнаты для обновления")],
    update_data: RoomUpdate,
    current_user: user_dependencies,
    room_serv: room_service,
    session_id: Annotated[str | None, Cookie()] = None,
) -> RoomResponse:
    """
    Обновляет информацию о комнате по ее ID.
    Требуется аутентификация. Только владелец комнаты может ее обновить.
    """
    update_data = update_data.model_dump(exclude_unset=True)
    current_user.set_session_id = session_id
    user_from_identity = current_user.get_current_user()
    return room_serv.update_room(room_id, update_data, user_from_identity)


@room.delete(
    "/{room_id}",
    status_code=status.HTTP_200_OK,
)
@inject
def delete_room(
    room_id: Annotated[uuid.UUID, Path(..., description="ID комнаты для удаления")],
    current_user: user_dependencies,
    room_serv: room_service,
    session_id: Annotated[str | None, Cookie()] = None,
) -> dict:
    """
    Удаляет комнату по ее ID.
    Требуется аутентификация. Только владелец комнаты может ее удалить.
    """
    current_user.set_session_id = session_id
    user_from_identity = current_user.get_current_user()
    return room_serv.delete_room(room_id, user_from_identity)




@room.get(
    "/by-name/",
    response_model=RoomResponse,
)
@inject
async def get_room_by_name(
    name: Annotated[str, Query(..., description="Название комнаты")],
    room_serv: room_service,
    redis_client: redis_service,
) -> RoomResponse:
    """
    Получает информацию о комнате по ее названию.
    Не требует аутентификации.
    """
    key = f'rooms:get_room_by_name:{name}'
    async def fetch():
        return await room_serv.get_room_by_name(name)
    return await redis_client.get_or_set(key,fetch,300)


@room.get(
    "/my-rooms",
    response_model=list[RoomResponse],
)
@inject
async def get_my_rooms(
    current_user: user_dependencies,room_serv: room_service, redis_client: redis_service,session_id: Annotated[str | None, Cookie()] = None,
) -> list[RoomResponse]:
    """
    Получает список всех комнат, в которых состоит текущий аутентифицированный пользователь.
    Требуется аутентификация.
    """
    current_user.set_session_id = session_id
    user_from_identity = current_user.get_current_user()
    key = f'rooms:get_my_rooms:{user_from_identity.id}'
    async def fetch():
        return await room_serv.get_user_rooms(user_from_identity)
    return await redis_client.get_or_set(key,fetch,300)

@room.get(
    "/",
    response_model=list[RoomResponse],
)
@inject
async def get_all_rooms(
    room_serv: room_service,
) -> list[RoomResponse]:
    """
    Получает список всех доступных комнат.
    Не требует аутентификации.
    """
    return await room_serv.get_all_rooms()


@room.get(
    "/{room_id}",
    response_model=RoomResponse,
)
@inject
async def get_room_by_id(
    room_id: Annotated[uuid.UUID, Path(..., description="Уникальный ID комнаты")],
    room_serv: room_service,
    redis_client: redis_service,
) -> RoomResponse:
    """
    Получает информацию о комнате по ее ID.
    Не требует аутентификации.
    """
    key = f'rooms:get_room_by_id:{room_id}'
    async def fetch():
        return await room_serv.get_room_by_id(room_id)
    return await redis_client.get_or_set(key,fetch,300)