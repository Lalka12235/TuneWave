from fastapi import APIRouter,Query
from typing import Annotated,Any
from app.services.spotify_public_service import SpotifyPublicService
from fastapi_limiter.depends import RateLimiter


spotify_public = APIRouter(
    tags=['Spotify public'],
    prefix='/spotify-public'
)

@spotify_public.get('/search/tracks',response_model=dict[str,Any])
async def search_public_track(
    query: Annotated[str, Query(description='Поисковый запрос для треков Spotify')],
    limit: Annotated[int, Query(ge=1, le=50, description="Максимальное количество результатов")] = 10,
) -> dict[str,Any]:
    """
    Ищет треки на Spotify по заданному запросу.
    Без аутентификации пользователя в вашем приложении и наличия привязанного аккаунта Spotify.
    """
    spotify = SpotifyPublicService()
    search_results = await spotify.search_public_track(query,limit)
    return search_results