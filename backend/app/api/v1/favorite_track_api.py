from fastapi import APIRouter,Depends,Path,status
from app.services.favorite_track_service import FavoriteTrackService
from app.schemas.favorite_track_schemas import FavoriteTrackResponse,FavoriteTrackAdd
from app.config.session import get_db
from sqlalchemy.orm import Session
from app.models.user import User
from app.auth.auth import get_current_user
from typing import Annotated,Any
from fastapi_limiter.depends import RateLimiter
import uuid


ft = APIRouter(
    tags=['Favorite Track'],
    prefix='/favorites'
)

db_dependencies = Annotated[Session,Depends(get_db)]
user_dependencies = Annotated[User,Depends(get_current_user)]


@ft.get('/me',response_model=list[FavoriteTrackResponse],dependencies=[Depends(RateLimiter(times=15, seconds=60))])
async def get_user_favorite_tracks(
    db: db_dependencies,
    user: user_dependencies,
    
) -> list[FavoriteTrackResponse]:
    """
    Получает список всех любимых треков текущего аутентифицированного пользователя.
    
    Args:
        db (Session): Сессия базы данных.
        user (User): Текущий аутентифицированный пользователь.

    Returns:
        list[FavoriteTrackResponse]: Список любимых треков пользователя.
    """
    return FavoriteTrackService.get_user_favorite_tracks(db,user.id)


@ft.post('/me',response_model=FavoriteTrackResponse,status_code=status.HTTP_201_CREATED,dependencies=[Depends(RateLimiter(times=5, seconds=60))])
async def add_favorite_track(
    db: db_dependencies,
    user: user_dependencies,
    add_data: FavoriteTrackAdd,
    dependencies=[Depends(RateLimiter(times=5, seconds=60))],
) -> FavoriteTrackResponse:
    """
    Добавляет трек в список любимых треков текущего аутентифицированного пользователя.

    Args:
        db (Session): Сессия базы данных.
        user (User): Текущий аутентифицированный пользователь.
        add_data (FavoriteTrackAdd): Pydantic-модель, содержащая spotify_id трека.

    Returns:
        FavoriteTrackResponse: Объект, представляющий добавленный любимый трек.
    """
    return FavoriteTrackService.add_favorite_track(db,user.id,add_data.spotify_id)


@ft.delete('/me{spotify_id}', response_model=dict[str,Any],dependencies=[Depends(RateLimiter(times=5, seconds=60))])
async def remvoe_favorite_track(
    db: db_dependencies,
    user: user_dependencies,
    spotify_id: Annotated[str,Path(...,description='Spotify ID трека для удаления из избранного')],
    dependencies=[Depends(RateLimiter(times=5, seconds=60))],
) -> dict[str,Any]:
    """
    Добавляет трек в список любимых треков текущего аутентифицированного пользователя.

    Args:
        db (Session): Сессия базы данных.
        user (User): Текущий аутентифицированный пользователь.
        add_data (FavoriteTrackAdd): Pydantic-модель, содержащая spotify_id трека.

    Returns:
        FavoriteTrackResponse: Объект, представляющий добавленный любимый трек.
    """
    return FavoriteTrackService.remove_favorite_track(db,user.id,)


@ft.get('/{user_id}', response_model=list[FavoriteTrackResponse],
        dependencies=[Depends(RateLimiter(times=10, seconds=60))])
async def get_user_favorite_tracks_public(
    user_id: Annotated[uuid.UUID, Path(..., description="ID пользователя, чьи любимые треки нужно получить")],
    db: db_dependencies,
) -> list[FavoriteTrackResponse]:
    """
    Получает список любимых треков указанного пользователя.
    Этот маршрут доступен публично (без аутентификации).

    Args:
        user_id (uuid.UUID): ID пользователя.
        db (Session): Сессия базы данных.

    Returns:
        list[FavoriteTrackResponse]: Список любимых треков пользователя.
    """
    return await FavoriteTrackService.get_user_favorite_tracks(db, user_id)