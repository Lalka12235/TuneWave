import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Path, status
from fastapi_limiter.depends import RateLimiter

from app.auth.auth import get_current_user
from app.schemas.entity import UserEntity
from app.schemas.favorite_track_schemas import FavoriteTrackAdd, FavoriteTrackResponse
from app.services.favorite_track_service import FavoriteTrackService
from app.services.dep import get_favorite_track_service
from app.services.redis_service import RedisService
from app.services.dep import get_redis_client

ft = APIRouter(
    tags=['Favorite Track'],
    prefix='/favorites'
)

user_dependencies = Annotated[UserEntity,Depends(get_current_user)]
favorite_track_service = Annotated[FavoriteTrackService,Depends(get_favorite_track_service)]
redis_service = Annotated[RedisService,Depends(get_redis_client)]


@ft.get('/me',response_model=list[FavoriteTrackResponse],dependencies=[Depends(RateLimiter(times=15, seconds=60))])
async def get_user_favorite_tracks(
    favorite_track_service: favorite_track_service,
    user: user_dependencies,
    redis_client: redis_service
) -> list[FavoriteTrackResponse]:
    """
    Получает список всех любимых треков текущего аутентифицированного пользователя.
    
    Args:
        user (User): Текущий аутентифицированный пользователь.

    Returns:
        list[FavoriteTrackResponse]: Список любимых треков пользователя.
    """
    key = f'favorite_track:get_user_favorite_track:{user.id}'
    async def fetch():
        return favorite_track_service.get_user_favorite_tracks(user.id)
    return await redis_client.get_or_set(key,fetch,300)


@ft.post('/me',response_model=FavoriteTrackResponse,status_code=status.HTTP_201_CREATED,dependencies=[Depends(RateLimiter(times=5, seconds=60))])
async def add_favorite_track(
    favorite_track_service: favorite_track_service,
    user: user_dependencies,
    add_data: FavoriteTrackAdd,
) -> FavoriteTrackResponse:
    """
    Добавляет трек в список любимых треков текущего аутентифицированного пользователя.

    Args:
        user (User): Текущий аутентифицированный пользователь.
        add_data (FavoriteTrackAdd): Pydantic-модель, содержащая spotify_id трека.

    Returns:
        FavoriteTrackResponse: Объект, представляющий добавленный любимый трек.
    """
    return await favorite_track_service.add_favorite_track(user.id,add_data.spotify_id)


@ft.delete('/me{spotify_id}', response_model=dict[str,Any],dependencies=[Depends(RateLimiter(times=5, seconds=60))])
async def remvoe_favorite_track(
    favorite_track_service: favorite_track_service,
    user: user_dependencies,
    spotify_id: Annotated[str,Path(...,description='Spotify ID трека для удаления из избранного')],
) -> dict[str,Any]:
    """
    Добавляет трек в список любимых треков текущего аутентифицированного пользователя.

    Args:
        user (User): Текущий аутентифицированный пользователь.
        add_data (FavoriteTrackAdd): Pydantic-модель, содержащая spotify_id трека.

    Returns:
        FavoriteTrackResponse: Объект, представляющий добавленный любимый трек.
    """
    return favorite_track_service.remove_favorite_track(user.id,spotify_id)


@ft.get('/{user_id}', response_model=list[FavoriteTrackResponse],
        dependencies=[Depends(RateLimiter(times=10, seconds=60))])
async def get_user_favorite_tracks_public(
    favorite_track_service: favorite_track_service,
    user_id: Annotated[uuid.UUID, Path(..., description="ID пользователя, чьи любимые треки нужно получить")],
    redis_client: redis_service
) -> list[FavoriteTrackResponse]:
    """
    Получает список любимых треков указанного пользователя.
    Этот маршрут доступен публично (без аутентификации).

    Args:
        user_id (uuid.UUID): ID пользователя.

    Returns:
        list[FavoriteTrackResponse]: Список любимых треков пользователя.
    """
    key = f'favorite_track:get_user_favorite_track_public:{user_id}'
    async def fetch():
        return favorite_track_service.get_user_favorite_tracks(user_id)
    return await redis_client.get_or_set(key,fetch,300)