from fastapi import APIRouter, Depends,Path
from app.services.track_service import TrackService
from typing import Annotated
from app.config.session import get_db
from sqlalchemy.orm import Session
from app.schemas.track_schemas import TrackBase,TrackCreate
from fastapi_limiter.depends import RateLimiter


track = APIRouter(
    tags=['Track'],
    prefix='/track'
)


db_dependencies = Annotated[Session,Depends(get_db)]


@track.get('/{spotify_id}',response_model=TrackBase,dependencies=[Depends(RateLimiter(times=15, seconds=60))])
async def get_track_by_id(
    spotify_id: Annotated[str,Path(...,description='Уникальный ID трека')],
    db: db_dependencies,
) -> TrackBase:
    """
    Находит трек по ID в базе данных
    """
    return TrackService.get_track_by_Spotify_id(db,spotify_id)


@track.post('/',response_model=TrackCreate,dependencies=[Depends(RateLimiter(times=10, seconds=60))])
async def create_track_from_spotify_data(
    db: db_dependencies,
    spotify_data: TrackCreate,
) -> TrackCreate:
    """
    Создает трек в базе данных на основе Spotify data
    """
    return await TrackService.get_or_create_track(db,spotify_data)

