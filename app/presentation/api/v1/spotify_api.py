from typing import Annotated, Any

from app.application.services.spotify_service import SpotifyService
from fastapi import APIRouter, Cookie,Query,Depends

from app.domain.entity import UserEntity
from app.presentation.dependencies import get_spotify_service
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
    spotify_service: Annotated[SpotifyService,Depends(get_spotify_service)],
    limit: Annotated[int, Query(ge=1, le=50, description="Максимальное количество результатов")] = 10,
    session_id: Annotated[str | None, Cookie()] = None,
) -> dict[str,Any]:
    """
    Ищет треки на Spotify по заданному запросу.
    Требует аутентификации пользователя в вашем приложении и наличия привязанного аккаунта Spotify.
    """
    current_user.set_session_id = session_id
    user_from_identity = current_user.get_current_user()
    spotify_service.set_user = user_from_identity

    return await spotify_service.search_track(query,limit)