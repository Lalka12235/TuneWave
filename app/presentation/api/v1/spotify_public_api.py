from typing import Annotated

from fastapi import APIRouter, Query

from app.infrastructure.external.spotify.spotify_public_service import SpotifyPublicService
from dishka.integrations.fastapi import DishkaRoute,FromDishka


spotify_public = APIRouter(
    tags=['Spotify public'],
    prefix='/spotify-public',
    route_class=DishkaRoute,
)

@spotify_public.get('/search/tracks',response_model=list[SpotifyPublicService])
async def search_public_track(
    spotify: FromDishka[SpotifyPublicService],
    query: Annotated[str, Query(description='Поисковый запрос для треков Spotify')],
    limit: Annotated[int, Query(ge=1, le=50, description="Максимальное количество результатов")] = 10,
) -> list[SpotifyPublicService]:
    """
    Ищет треки на Spotify по заданному запросу.
    Без аутентификации пользователя в вашем приложении и наличия привязанного аккаунта Spotify.
    """
    search_results = await spotify.search_public_track(query,limit)
    return search_results