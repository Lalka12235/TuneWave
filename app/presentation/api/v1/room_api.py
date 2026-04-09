import uuid
from typing import Annotated

from fastapi import APIRouter, Path, Query, status


from app.domain.entity import UserEntity,RoomEntity
from app.infrastructure.redis.redis_service import RedisService
from app.presentation.schemas.room_schemas import (
    RoomCreate,
    RoomResponse,
    RoomUpdate,
)

from dishka.integrations.fastapi import DishkaRoute,FromDishka
from app.application.commands.room import ReadRoom,CreateRoom,DeleteRoom,UpdateRoom

room = APIRouter(tags=["Room"], prefix="/rooms",route_class=DishkaRoute)

user_dependencies = FromDishka[UserEntity]
redis_service = FromDishka[RedisService]

def convert_entity_to_schema(entity: RoomEntity) -> RoomResponse:
    return RoomResponse(
        id=entity.id,
        name=entity.name,
        max_members=entity.max_members,
        is_private=entity.is_private,
        owner_id=entity.owner_id,
        created_at=entity.created_at,
        current_track_id=entity.current_track_id,
        current_track_position_ms=entity.current_track_position_ms,
        is_playing=entity.is_playing,
        #queue=
        #owner=
    )

@room.post(
    "/",
    response_model=RoomResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_room(
    room_data: RoomCreate,
    current_user: user_dependencies,
    interactor: FromDishka[CreateRoom],
) -> RoomResponse:
    """
    Создает новую комнату.
    Требуется аутентификация. Владелец комнаты будет текущим аутентифицированным пользователем.
    """
    room_data = room_data.model_dump()
    result = await interactor.create_room(room_data, current_user)
    return convert_entity_to_schema(result)


@room.put(
    "/{room_id}",
    response_model=RoomResponse,
)
def update_room(
    room_id: Annotated[uuid.UUID, Path(..., description="ID комнаты для обновления")],
    update_data: RoomUpdate,
    current_user: user_dependencies,
    interactor: FromDishka[UpdateRoom],
) -> RoomResponse:
    """
    Обновляет информацию о комнате по ее ID.
    Требуется аутентификация. Только владелец комнаты может ее обновить.
    """
    update_data = update_data.model_dump(exclude_unset=True)
    result = interactor.update_room(room_id, update_data, current_user)
    return convert_entity_to_schema(result)


@room.delete(
    "/{room_id}",
    status_code=status.HTTP_200_OK,
)
def delete_room(
    room_id: Annotated[uuid.UUID, Path(..., description="ID комнаты для удаления")],
    current_user: user_dependencies,
    interactor: FromDishka[DeleteRoom],
) -> dict[str,str]:
    """
    Удаляет комнату по ее ID.
    Требуется аутентификация. Только владелец комнаты может ее удалить.
    """
    return interactor.delete_room(room_id, current_user)

@room.get(
    "/by-name/",
    response_model=RoomResponse,
)
async def get_room_by_name(
    name: Annotated[str, Query(..., description="Название комнаты")],
    interactor: FromDishka[ReadRoom],
    redis_client: redis_service,
) -> RoomResponse:
    """
    Получает информацию о комнате по ее названию.
    Не требует аутентификации.
    """
    key = f'rooms:get_room_by_name:{name}'
    async def fetch():
        result = await interactor.get_room_by_name(name)
        return convert_entity_to_schema(result)
    return await redis_client.get_or_set(key,fetch,300)


@room.get(
    "/my-rooms",
    response_model=list[RoomResponse],
)
async def get_my_rooms(
    current_user: user_dependencies,interactor: FromDishka[ReadRoom], redis_client: redis_service
) -> list[RoomResponse]:
    """
    Получает список всех комнат, в которых состоит текущий аутентифицированный пользователь.
    Требуется аутентификация.
    """
    key = f'rooms:get_my_rooms:{current_user.id}'
    async def fetch():
        result = await interactor.get_user_rooms(current_user)
        return [convert_entity_to_schema(res) for res in result]
    return await redis_client.get_or_set(key,fetch,300)

@room.get(
    "/",
    response_model=list[RoomResponse],
)
async def get_all_rooms(
    interactor: FromDishka[ReadRoom],
) -> list[RoomResponse]:
    """
    Получает список всех доступных комнат.
    Не требует аутентификации.
    """
    result = await interactor.get_all_rooms()
    return [convert_entity_to_schema(res) for res in result]


@room.get(
    "/{room_id}",
    response_model=RoomResponse,
)
async def get_room_by_id(
    room_id: Annotated[uuid.UUID, Path(..., description="Уникальный ID комнаты")],
    interactor: FromDishka[ReadRoom],
    redis_client: redis_service,
) -> RoomResponse:
    """
    Получает информацию о комнате по ее ID.
    Не требует аутентификации.
    """
    key = f'rooms:get_room_by_id:{room_id}'
    async def fetch():
        result = await interactor.get_room_by_id(room_id)
        return convert_entity_to_schema(result)
    return await redis_client.get_or_set(key,fetch,300)