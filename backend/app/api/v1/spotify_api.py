from fastapi import APIRouter, Depends,Query
from sqlalchemy.orm import Session
from typing import Annotated,Any
from app.config.session import get_db
from app.auth.auth import get_current_user
from app.models.user import User
from backend.app.services.spotify_service import SpotifyService
from app.services.spotify_public_service import SpotifyPublicService


spotify = APIRouter(
    tags=['Spotify'],
    prefix='/spotify'
)


db_dependencies = Annotated[Session,Depends(get_db)]
user_dependencies = Annotated[User, Depends(get_current_user)]


@spotify.get('/search/tracks',response_model=dict[str,Any])
async def search_spotify_tracks(
    query: Annotated[str, Query(description='Поисковый запрос для треков Spotify')],
    db: db_dependencies,
    current_user: user_dependencies,
    spotify_public: SpotifyPublicService = Depends(),
    limit: Annotated[int, Query(ge=1, le=50, description="Максимальное количество результатов")] = 10,
) -> dict[str,Any]:
    """
    Ищет треки на Spotify по заданному запросу.
    Требует аутентификации пользователя в вашем приложении и наличия привязанного аккаунта Spotify.
    """
    spotify_service = SpotifyService(db=db, user=current_user,spotify_public=spotify_public)
    search_results = await spotify_service.smart_search_tracks(query,limit)

    return search_results