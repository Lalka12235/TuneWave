from fastapi import APIRouter, Depends,Query
from sqlalchemy.orm import Session
from typing import Annotated,Any
from app.config.session import get_db
from app.auth.auth import get_current_user
from app.models.user import User
from app.services.spotify_public_service import SpotifyPublicService
import uuid

spotify_public = APIRouter(
    tags=['Spotify Public'],
    prefix='/spotify'
)


@spotify_public.get('/search-public/tracks',response_model=dict[str,Any])
async def search_spotify_public(
    query: Annotated[str, Query(description='Поисковый запрос для треков Spotify')],
    limit: Annotated[int, Query(ge=1, le=50, description="Максимальное количество результатов")] = 10,
) -> dict[str,Any]:
    """
    Ищет треки на Spotify по заданному запросу.
    Не требует аутентификации пользователя.
    """
    spotify = SpotifyPublicService()
    search_results = await spotify.search_public_track(query=query,limit=limit)
    return search_results
