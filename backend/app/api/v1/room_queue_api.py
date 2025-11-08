import uuid
from typing import Annotated

from fastapi import APIRouter,Depends, Path,status
from fastapi_limiter.depends import RateLimiter

from app.auth.auth import get_current_user
from app.schemas.entity import UserEntity
from app.schemas.room_schemas import (
    AddTrackToQueueRequest,
    TrackInQueueResponse,
)
from app.services.room_queue_service import RoomQueueService
from app.services.dep import get_room_queue_service

from app.services.redis_service import RedisService
from app.services.dep import get_redis_client

room_queue = APIRouter(tags=["Room"], prefix="/rooms")

user_dependencies = Annotated[UserEntity, Depends(get_current_user)]
redis_service = Annotated[RedisService,Depends(get_redis_client)]
room_queue_service = Annotated[RoomQueueService,Depends(get_room_queue_service)]

@room_queue.post(
    "/{room_id}/queue",
    response_model=TrackInQueueResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RateLimiter(times=10, seconds=60))],
)
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
    dependencies=[Depends(RateLimiter(times=10, seconds=60))],
)
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
    dependencies=[Depends(RateLimiter(times=10, seconds=60))],
)
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