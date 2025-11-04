import json
import uuid
from typing import Annotated,Callable

from fastapi import APIRouter,Depends, Path,status
from fastapi_limiter.depends import RateLimiter
from infrastructure.redis.redis import get_redis_client
from redis.asyncio import Redis

from app.auth.auth import get_current_user
from app.logger.log_config import logger
from app.models import User
from app.schemas.room_schemas import (
    AddTrackToQueueRequest,
    TrackInQueueResponse,
)
from app.services.room_queue_service import RoomQueueService
from app.services.dep import get_room_queue_service

room_queue = APIRouter(tags=["Room"], prefix="/rooms")

user_dependencies = Annotated[User, Depends(get_current_user)]

def cache(key_generator: Callable, expiration: int = 300):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Извлекаем redis_client из kwargs (он будет добавлен FastAPI)
            redis_client: Redis = kwargs.get("redis_client")

            # Если Redis недоступен, выполняем функцию без кэширования
            if not redis_client:
                logger.warning("Redis client not available, skipping cache...")
                return await func(*args, **kwargs)

            # ✅ Используем переданную функцию-генератор для создания ключа
            try:
                cache_key = key_generator(*args, **kwargs)
            except Exception as e:
                logger.error(
                    f"Error generating cache key: {e}. Skipping cache...", exc_info=True
                )
                return await func(*args, **kwargs)

            # 1. Пробуем получить данные из кэша
            cached_data = await redis_client.get(cache_key)
            if cached_data:
                logger.info(f"Cache hit for key: {cache_key}")
                return json.loads(cached_data)

            # 2. Если данных в кэше нет, выполняем оригинальную функцию
            logger.info(f"Cache miss for key: {cache_key}. Fetching from DB...")
            result = await func(*args, **kwargs)

            await redis_client.setex(cache_key, expiration, json.dumps(result))
            return result

        return wrapper

    return decorator

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
    room_queue_service: Annotated[RoomQueueService,Depends(get_room_queue_service)],
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
    room_queue_service: Annotated[RoomQueueService,Depends(get_room_queue_service)],
    redis_client: Annotated[Redis,Depends(get_redis_client)],
) -> list[TrackInQueueResponse]:
    """
    Получает текущую очередь треков для комнаты.
    """
    return room_queue_service.get_room_queue(room_id)


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
    room_queue_service: Annotated[RoomQueueService,Depends(get_room_queue_service)],
) -> dict:
    """
    Удаляет трек из очереди комнаты по ID ассоциации. Только владелец комнаты может это сделать.
    """
    return await room_queue_service.remove_track_from_queue(
        room_id, association_id, current_user.id
    )