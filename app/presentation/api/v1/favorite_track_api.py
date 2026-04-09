import uuid
from typing import Annotated

from fastapi import APIRouter, Path, status

from app.domain.entity import UserEntity,FavoriteTrackEntity
from app.infrastructure.redis.redis_service import RedisService
from app.presentation.schemas.favorite_track_schemas import FavoriteTrackAdd, FavoriteTrackResponse
from dishka.integrations.fastapi import DishkaRoute,FromDishka
from app.application.commands.favorite_track import ReadFavoriteTrack,CreateTrackFavorite,DeleteFavoriteTrack

ft = APIRouter(
    tags=['Favorite Track'],
    prefix='/favorites',
    route_class=DishkaRoute
)

user_dependencies = FromDishka[UserEntity]

def convert_entity_to_schema(entity: FavoriteTrackEntity) -> FavoriteTrackResponse:
    return FavoriteTrackResponse(
        id=entity.id,
        track_id=entity.track_id,
        added_at=entity.added_at,
        #track=entity.track
    )

@ft.get('/me',response_model=list[FavoriteTrackResponse])
async def get_user_favorite_tracks(
    interactor: FromDishka[ReadFavoriteTrack],
    user: user_dependencies,
    redis_client: FromDishka[RedisService],
) -> list[FavoriteTrackResponse]:
    """
    Получает список всех любимых треков текущего аутентифицированного пользователя.
    """
    key = f'favorite_track:get_user_favorite_track:{user.id}'
    async def fetch():
        result = interactor.get_user_favorite_tracks(user.id)
        return [convert_entity_to_schema(res) for res in result]
    return await redis_client.get_or_set(key,fetch,300)


@ft.post('/me',response_model=FavoriteTrackResponse,status_code=status.HTTP_201_CREATED)
async def add_favorite_track(
    interactor: FromDishka[CreateTrackFavorite],
    user: user_dependencies,
    add_data: FavoriteTrackAdd,
) -> FavoriteTrackResponse:
    """
    Добавляет трек в список любимых треков текущего аутентифицированного пользователя.
    """
    result = await interactor.add_favorite_track(user.id,add_data.spotify_id)
    return convert_entity_to_schema(result)


@ft.delete('/me{spotify_id}', response_model=dict[str,str])
async def remove_favorite_track(
    interactor: FromDishka[DeleteFavoriteTrack],
    user: user_dependencies,
    spotify_id: Annotated[str,Path(...,description='Spotify ID трека для удаления из избранного')],
) -> dict[str,str]:
    """
    Добавляет трек в список любимых треков текущего аутентифицированного пользователя.
    """
    return interactor.remove_favorite_track(user.id,spotify_id)


@ft.get('/{user_id}', response_model=list[FavoriteTrackResponse])
async def get_user_favorite_tracks_public(
    interactor: FromDishka[ReadFavoriteTrack],
    user_id: Annotated[uuid.UUID, Path(..., description="ID пользователя, чьи любимые треки нужно получить")],
    redis_client: FromDishka[RedisService],
) -> list[FavoriteTrackResponse]:
    """
    Получает список любимых треков указанного пользователя.
    Этот маршрут доступен публично (без аутентификации).
    """
    key = f'favorite_track:get_user_favorite_track_public:{user_id}'
    async def fetch():
        result = interactor.get_user_favorite_tracks(user_id)
        return [convert_entity_to_schema(res) for res in result]
    return await redis_client.get_or_set(key,fetch,300)