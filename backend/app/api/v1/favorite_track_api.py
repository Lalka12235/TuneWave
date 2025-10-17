from fastapi import APIRouter,Depends,Path,status
from app.services.favorite_track_service import FavoriteTrackService
from app.schemas.favorite_track_schemas import FavoriteTrackResponse,FavoriteTrackAdd
from app.config.session import get_db
from sqlalchemy.orm import Session
from app.models.user import User
from app.auth.auth import get_current_user
from typing import Annotated,Any
from fastapi_limiter.depends import RateLimiter
import uuid
from infrastructure.redis.redis import get_redis_client
from redis.asyncio import Redis
from app.logger.log_config import logger
import json
from typing import Callable

ft = APIRouter(
    tags=['Favorite Track'],
    prefix='/favorites'
)

db_dependencies = Annotated[Session,Depends(get_db)]
user_dependencies = Annotated[User,Depends(get_current_user)]


def cache(key_generator: Callable, expiration: int = 300):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Извлекаем redis_client из kwargs (он будет добавлен FastAPI)
            redis_client: Redis = kwargs.get('redis_client')
            
            # Если Redis недоступен, выполняем функцию без кэширования
            if not redis_client:
                logger.warning("Redis client not available, skipping cache...")
                return await func(*args, **kwargs)

            # ✅ Используем переданную функцию-генератор для создания ключа
            try:
                cache_key = key_generator(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error generating cache key: {e}. Skipping cache...", exc_info=True)
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

@ft.get('/me',response_model=list[FavoriteTrackResponse],dependencies=[Depends(RateLimiter(times=15, seconds=60))])
@cache(key_generator=lambda user, **kwargs: f"user_me_favorite_track:{user.id}", expiration=300)
async def get_user_favorite_tracks(
    db: db_dependencies,
    user: user_dependencies,
    redis_client: Redis = Depends(get_redis_client) 
) -> list[FavoriteTrackResponse]:
    """
    Получает список всех любимых треков текущего аутентифицированного пользователя.
    
    Args:
        db (Session): Сессия базы данных.
        user (User): Текущий аутентифицированный пользователь.

    Returns:
        list[FavoriteTrackResponse]: Список любимых треков пользователя.
    """
    return FavoriteTrackService.get_user_favorite_tracks(db,user.id)


@ft.post('/me',response_model=FavoriteTrackResponse,status_code=status.HTTP_201_CREATED,dependencies=[Depends(RateLimiter(times=5, seconds=60))])
async def add_favorite_track(
    db: db_dependencies,
    user: user_dependencies,
    add_data: FavoriteTrackAdd,
) -> FavoriteTrackResponse:
    """
    Добавляет трек в список любимых треков текущего аутентифицированного пользователя.

    Args:
        db (Session): Сессия базы данных.
        user (User): Текущий аутентифицированный пользователь.
        add_data (FavoriteTrackAdd): Pydantic-модель, содержащая spotify_id трека.

    Returns:
        FavoriteTrackResponse: Объект, представляющий добавленный любимый трек.
    """
    return await FavoriteTrackService.add_favorite_track(db,user.id,add_data.spotify_id)


@ft.delete('/me{spotify_id}', response_model=dict[str,Any],dependencies=[Depends(RateLimiter(times=5, seconds=60))])
async def remvoe_favorite_track(
    db: db_dependencies,
    user: user_dependencies,
    spotify_id: Annotated[str,Path(...,description='Spotify ID трека для удаления из избранного')],
) -> dict[str,Any]:
    """
    Добавляет трек в список любимых треков текущего аутентифицированного пользователя.

    Args:
        db (Session): Сессия базы данных.
        user (User): Текущий аутентифицированный пользователь.
        add_data (FavoriteTrackAdd): Pydantic-модель, содержащая spotify_id трека.

    Returns:
        FavoriteTrackResponse: Объект, представляющий добавленный любимый трек.
    """
    return FavoriteTrackService.remove_favorite_track(db,user.id,spotify_id)


@ft.get('/{user_id}', response_model=list[FavoriteTrackResponse],
        dependencies=[Depends(RateLimiter(times=10, seconds=60))])
@cache(key_generator=lambda user_id, **kwargs: f"user_favorite_track:{user_id}", expiration=300)
async def get_user_favorite_tracks_public(
    user_id: Annotated[uuid.UUID, Path(..., description="ID пользователя, чьи любимые треки нужно получить")],
    db: db_dependencies,
    redis_client: Redis = Depends(get_redis_client) 
) -> list[FavoriteTrackResponse]:
    """
    Получает список любимых треков указанного пользователя.
    Этот маршрут доступен публично (без аутентификации).

    Args:
        user_id (uuid.UUID): ID пользователя.
        db (Session): Сессия базы данных.

    Returns:
        list[FavoriteTrackResponse]: Список любимых треков пользователя.
    """
    return FavoriteTrackService.get_user_favorite_tracks(db, user_id)