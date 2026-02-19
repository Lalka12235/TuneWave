import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Cookie, Path, status

from app.domain.entity import UserEntity
from app.presentation.schemas.favorite_track_schemas import FavoriteTrackAdd, FavoriteTrackResponse
from app.application.services.favorite_track_service import FavoriteTrackService
from app.application.services.redis_service import RedisService

from dishka.integrations.fastapi import DishkaRoute,FromDishka,inject

ft = APIRouter(
    tags=['Favorite Track'],
    prefix='/favorites',
    route_class=DishkaRoute
)

user_dependencies = FromDishka[UserEntity]
favorite_track_service = FromDishka[FavoriteTrackService]
redis_service =FromDishka[RedisService]


@ft.get('/me',response_model=list[FavoriteTrackResponse])
@inject
async def get_user_favorite_tracks(
    favorite_track_service: favorite_track_service,
    user: user_dependencies,
    redis_client: redis_service,
    session_id: Annotated[str | None, Cookie()] = None,
) -> list[FavoriteTrackResponse]:
    """
    Получает список всех любимых треков текущего аутентифицированного пользователя.
    
    Args:
        user (User): Текущий аутентифицированный пользователь.

    Returns:
        list[FavoriteTrackResponse]: Список любимых треков пользователя.
    """
    user.set_session_id = session_id
    user_from_identity = user.get_current_user()
    key = f'favorite_track:get_user_favorite_track:{user_from_identity.id}'
    async def fetch():
        return favorite_track_service.get_user_favorite_tracks(user_from_identity.id)
    return await redis_client.get_or_set(key,fetch,300)


@ft.post('/me',response_model=FavoriteTrackResponse,status_code=status.HTTP_201_CREATED)
@inject
async def add_favorite_track(
    favorite_track_service: favorite_track_service,
    user: user_dependencies,
    add_data: FavoriteTrackAdd,
    session_id: Annotated[str | None, Cookie()] = None,
) -> FavoriteTrackResponse:
    """
    Добавляет трек в список любимых треков текущего аутентифицированного пользователя.

    Args:
        user (User): Текущий аутентифицированный пользователь.
        add_data (FavoriteTrackAdd): Pydantic-модель, содержащая spotify_id трека.

    Returns:
        FavoriteTrackResponse: Объект, представляющий добавленный любимый трек.
    """
    user.set_session_id = session_id
    user_from_identity = user.get_current_user()
    return await favorite_track_service.add_favorite_track(user_from_identity.id,add_data.spotify_id)


@ft.delete('/me{spotify_id}', response_model=dict[str,Any])
@inject
async def remvoe_favorite_track(
    favorite_track_service: favorite_track_service,
    user: user_dependencies,
    spotify_id: Annotated[str,Path(...,description='Spotify ID трека для удаления из избранного')],
    session_id: Annotated[str | None, Cookie()] = None,
) -> dict[str,Any]:
    """
    Добавляет трек в список любимых треков текущего аутентифицированного пользователя.

    Args:
        user (User): Текущий аутентифицированный пользователь.
        add_data (FavoriteTrackAdd): Pydantic-модель, содержащая spotify_id трека.

    Returns:
        FavoriteTrackResponse: Объект, представляющий добавленный любимый трек.
    """
    user.set_session_id = session_id
    user_from_identity = user.get_current_user()
    return favorite_track_service.remove_favorite_track(user_from_identity.id,spotify_id)


@ft.get('/{user_id}', response_model=list[FavoriteTrackResponse])
@inject
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