from typing import Annotated, Any

from app.services.spotify_service import SpotifyService
from fastapi import APIRouter, Depends, Query

from app.auth.auth import get_current_user
from app.schemas.entity import UserEntity

spotify = APIRouter(
    tags=['Spotify'],
    prefix='/spotify'
)

user_dependencies = Annotated[UserEntity, Depends(get_current_user)]


@spotify.get('/search/tracks',response_model=dict[str,Any])
async def search_spotify_tracks(
    query: Annotated[str, Query(description='Поисковый запрос для треков Spotify')],
    current_user: user_dependencies,
    limit: Annotated[int, Query(ge=1, le=50, description="Максимальное количество результатов")] = 10,
) -> dict[str,Any]:
    """
    Ищет треки на Spotify по заданному запросу.
    Требует аутентификации пользователя в вашем приложении и наличия привязанного аккаунта Spotify.
    """
    spotify_service = SpotifyService(user=current_user)

    return spotify_service.search_track(query,limit)