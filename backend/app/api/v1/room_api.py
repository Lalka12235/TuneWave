import uuid
from typing import Annotated

from fastapi import APIRouter,Depends, Path, Query, status
from fastapi_limiter.depends import RateLimiter


from app.auth.auth import get_current_user
from app.schemas.entity import UserEntity
from app.schemas.room_schemas import (
    RoomCreate,
    RoomResponse,
    RoomUpdate,
)
from app.services.room_service import RoomService
from app.services.dep import get_room_service

from app.services.redis_service import RedisService
from app.services.dep import get_redis_client

room = APIRouter(tags=["Room"], prefix="/rooms")

user_dependencies = Annotated[UserEntity, Depends(get_current_user)]
redis_service = Annotated[RedisService,Depends(get_redis_client)]
room_service = Annotated[RoomService,Depends(get_room_service)]


@room.post(
    "/",
    response_model=RoomResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RateLimiter(times=5, seconds=60))],
)
async def create_room(
    room_data: RoomCreate,
    current_user: user_dependencies,
    room_service: room_service,
) -> RoomResponse:
    """
    Создает новую комнату.
    Требуется аутентификация. Владелец комнаты будет текущим аутентифицированным пользователем.
    """
    return await room_service.create_room(room_data, current_user)


@room.put(
    "/{room_id}",
    response_model=RoomResponse,
    dependencies=[Depends(RateLimiter(times=10, seconds=60))],
)
def update_room(
    room_id: Annotated[uuid.UUID, Path(..., description="ID комнаты для обновления")],
    update_data: RoomUpdate,
    current_user: user_dependencies,
    room_service: room_service,
) -> RoomResponse:
    """
    Обновляет информацию о комнате по ее ID.
    Требуется аутентификация. Только владелец комнаты может ее обновить.
    """
    return room_service.update_room(room_id, update_data, current_user)


@room.delete(
    "/{room_id}",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(RateLimiter(times=10, seconds=60))],
)
def delete_room(
    room_id: Annotated[uuid.UUID, Path(..., description="ID комнаты для удаления")],
    current_user: user_dependencies,
    room_service: room_service,
) -> dict:
    """
    Удаляет комнату по ее ID.
    Требуется аутентификация. Только владелец комнаты может ее удалить.
    """
    return room_service.delete_room(room_id, current_user)


@room.post(
    "/{room_id}/join",
    response_model=RoomResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(RateLimiter(times=10, seconds=60))],
)


@room.get(
    "/by-name/",
    response_model=RoomResponse,
    dependencies=[Depends(RateLimiter(times=10, seconds=60))],
)
async def get_room_by_name(
    name: Annotated[str, Query(..., description="Название комнаты")],
    room_service: room_service,
    redis_client: redis_service,
) -> RoomResponse:
    """
    Получает информацию о комнате по ее названию.
    Не требует аутентификации.
    """
    key = f'rooms:get_room_by_name:{name}'
    async def fetch():
        return await room_service.get_room_by_name(name)
    return await redis_client.get_or_set(key,fetch,300)


@room.get(
    "/my-rooms",
    response_model=list[RoomResponse],
    dependencies=[Depends(RateLimiter(times=10, seconds=60))],
)
async def get_my_rooms(
    current_user: user_dependencies,room_service: room_service, redis_client: redis_service
) -> list[RoomResponse]:
    """
    Получает список всех комнат, в которых состоит текущий аутентифицированный пользователь.
    Требуется аутентификация.
    """
    key = f'rooms:get_my_rooms:{current_user.id}'
    async def fetch():
        return await room_service.get_user_rooms(current_user)
    return await redis_client.get_or_set(key,fetch,300)

@room.get(
    "/",
    response_model=list[RoomResponse],
    dependencies=[Depends(RateLimiter(times=10, seconds=60))],
)
async def get_all_rooms(
    room_service: room_service,
) -> list[RoomResponse]:
    """
    Получает список всех доступных комнат.
    Не требует аутентификации.
    """
    return await room_service.get_all_rooms()


@room.get(
    "/{room_id}",
    response_model=RoomResponse,
    dependencies=[Depends(RateLimiter(times=10, seconds=60))],
)
async def get_room_by_id(
    room_id: Annotated[uuid.UUID, Path(..., description="Уникальный ID комнаты")],
    room_service: room_service,
    redis_client: redis_service,
) -> RoomResponse:
    """
    Получает информацию о комнате по ее ID.
    Не требует аутентификации.
    """
    key = f'rooms:get_room_by_id:{room_id}'
    async def fetch():
        return await room_service.get_room_by_id(room_id)
    return await redis_client.get_or_set(key,fetch,300)