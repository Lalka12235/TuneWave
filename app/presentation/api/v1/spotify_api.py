from typing import Annotated, Any

from fastapi import APIRouter,Query

from app.domain.entity import UserEntity
from app.infrastructure.external.spotify.spotify_service import SpotifyService
from dishka.integrations.fastapi import DishkaRoute,FromDishka

spotify = APIRouter(
    tags=['Spotify'],
    prefix='/spotify',
    route_class=DishkaRoute
)

user_dependencies = FromDishka[UserEntity]


@spotify.get('/search/tracks',response_model=dict[str,Any])
async def search_spotify_tracks(
    query: Annotated[str, Query(description='Поисковый запрос для треков Spotify')],
    current_user: user_dependencies,
    spotify_service: FromDishka[SpotifyService],
    limit: Annotated[int, Query(ge=1, le=50, description="Максимальное количество результатов")] = 10,
) -> dict[str,Any]:
    """
    Ищет треки на Spotify по заданному запросу.
    Требует аутентификации пользователя в вашем приложении и наличия привязанного аккаунта Spotify.
    """
    spotify_service.set_user = current_user

    return await spotify_service.search_track(query,limit)