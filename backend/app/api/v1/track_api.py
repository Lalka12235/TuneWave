from typing import Annotated

from fastapi import APIRouter, Depends, Path
from fastapi_limiter.depends import RateLimiter


from app.schemas.track_schemas import TrackBase, TrackCreate
from app.services.track_service import TrackService
from app.services.dep import get_track_service

track = APIRouter(
    tags=['Track'],
    prefix='/track'
)


@track.get('/{spotify_id}',response_model=TrackBase,dependencies=[Depends(RateLimiter(times=15, seconds=60))])
async def get_track_by_id(
    spotify_id: Annotated[str,Path(...,description='Уникальный ID трека')],
    track_service: Annotated[TrackService,Depends(get_track_service)],
) -> TrackBase:
    """
    Находит трек по ID в базе данных
    """
    return track_service.get_track_by_Spotify_id(spotify_id)


@track.post('/',response_model=TrackCreate,dependencies=[Depends(RateLimiter(times=10, seconds=60))])
async def create_track_from_spotify_data(
    spotify_data: TrackCreate,
    track_service: Annotated[TrackService,Depends(get_track_service)],
) -> TrackCreate:
    """
    Создает трек в базе данных на основе Spotify data
    """
    return await track_service.get_or_create_track_from_spotify(spotify_data)

