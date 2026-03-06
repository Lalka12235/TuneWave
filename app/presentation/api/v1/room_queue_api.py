import uuid
from typing import Annotated

from fastapi import APIRouter, Path,status

from app.domain.entity import UserEntity
from app.infrastructure.redis.redis_service import RedisService
from app.presentation.schemas.room_schemas import (
    AddTrackToQueueRequest,
    TrackInQueueResponse,
)

from dishka.integrations.fastapi import DishkaRoute,FromDishka
from app.application.commands.room_queue import ReadRoomQueue,RemoveTrackFromQueue,AddTrackRoomQueue

room_queue = APIRouter(tags=["Room"], prefix="/rooms",route_class=DishkaRoute)


user_dependencies = FromDishka[UserEntity]
redis_service = FromDishka[RedisService]

@room_queue.post(
    "/{room_id}/queue",
    response_model=TrackInQueueResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_track_to_queue(
    current_user: user_dependencies,
    request: AddTrackToQueueRequest,
    room_id: Annotated[uuid.UUID, Path(..., description="Уникальный ID комнаты")],
    interactor: FromDishka[AddTrackRoomQueue],
) -> TrackInQueueResponse:
    """
    Добавляет трек в очередь комнаты. Только владелец комнаты может это сделать.
    """
    association = await interactor.add_track_to_queue(
        room_id=room_id, track_spotify_id=request.spotify_id, current_user=current_user
    )
    return association


@room_queue.get(
    "/{room_id}/queue/{association_id}",
    response_model=list[TrackInQueueResponse],
)
async def get_room_queue(
    room_id: Annotated[uuid.UUID, Path(..., description="Уникальный ID комнаты")],
    interactor: FromDishka[ReadRoomQueue],
    redis_client: redis_service,
) -> list[TrackInQueueResponse]:
    """
    Получает текущую очередь треков для комнаты.
    """
    key = f'rooms_queue:get_room_queue:{room_id}'
    async def fetch():
        return interactor.get_room_queue(room_id)
    return await redis_client.get_or_set(key,fetch,300)


@room_queue.delete(
    "/{room_id}/queue/{association_id}",
)
async def remove_track_from_queue(
    current_user: user_dependencies,
    room_id: Annotated[uuid.UUID, Path(..., description="Уникальный ID комнаты")],
    association_id: Annotated[
        uuid.UUID, Path(..., description="ID ассоциации трека в очереди")
    ],
    interactor: FromDishka[RemoveTrackFromQueue],
) -> dict:
    """
    Удаляет трек из очереди комнаты по ID ассоциации. Только владелец комнаты может это сделать.
    """
    return await interactor.remove_track_from_queue(
        room_id, association_id, current_user.id
    )