import uuid
from typing import Annotated

from fastapi import APIRouter, Path,status

from app.domain.entity import UserEntity
from app.presentation.schemas.room_schemas import (
    AddTrackToQueueRequest,
    TrackInQueueResponse,
)
from app.application.services.room_queue_service import RoomQueueService
from app.application.services.redis_service import RedisService

from dishka.integrations.fastapi import DishkaRoute,FromDishka,inject

room_queue = APIRouter(tags=["Room"], prefix="/rooms",route_class=DishkaRoute)

user_dependencies = FromDishka[UserEntity]
redis_service = FromDishka[RedisService]
room_queue_service = FromDishka[RoomQueueService]

@room_queue.post(
    "/{room_id}/queue",
    response_model=TrackInQueueResponse,
    status_code=status.HTTP_201_CREATED,
)
@inject
async def add_track_to_queue(
    current_user: user_dependencies,
    request: AddTrackToQueueRequest,
    room_id: Annotated[uuid.UUID, Path(..., description="Уникальный ID комнаты")],
    room_queue_service: room_queue_service,
) -> TrackInQueueResponse:
    """
    Добавляет трек в очередь комнаты. Только владелец комнаты может это сделать.
    """
    association = await room_queue_service.add_track_to_queue(
        room_id=room_id, track_spotify_id=request.spotify_id, current_user=current_user
    )
    return association


@room_queue.get(
    "/{room_id}/queue/{association_id}",
    response_model=list[TrackInQueueResponse],
)
@inject
async def get_room_queue(
    room_id: Annotated[uuid.UUID, Path(..., description="Уникальный ID комнаты")],
    room_queue_service: room_queue_service,
    redis_client: redis_service,
) -> list[TrackInQueueResponse]:
    """
    Получает текущую очередь треков для комнаты.
    """
    key = f'rooms_queue:get_room_queue:{room_id}'
    async def fetch():
        return room_queue_service.get_room_queue(room_id)
    return await redis_client.get_or_set(key,fetch,300)


@room_queue.delete(
    "/{room_id}/queue/{association_id}",
)
@inject
async def remove_track_from_queue(
    current_user: user_dependencies,
    room_id: Annotated[uuid.UUID, Path(..., description="Уникальный ID комнаты")],
    association_id: Annotated[
        uuid.UUID, Path(..., description="ID ассоциации трека в очереди")
    ],
    room_queue_service: room_queue_service,
) -> dict:
    """
    Удаляет трек из очереди комнаты по ID ассоциации. Только владелец комнаты может это сделать.
    """
    return await room_queue_service.remove_track_from_queue(
        room_id, association_id, current_user.id
    )