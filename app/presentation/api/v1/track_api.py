from typing import Annotated

from dishka import FromDishka
from fastapi import APIRouter, Depends, Path
from fastapi_limiter.depends import RateLimiter


from app.presentation.schemas.track_schemas import TrackBase, TrackCreate, TrackResponse
from app.application.services.track_service import TrackService

track_service = FromDishka[TrackService]

track = APIRouter(
    tags=['Track'],
    prefix='/track'
)


@track.get('/{spotify_id}',response_model=TrackBase,dependencies=[Depends(RateLimiter(times=15, seconds=60))])
async def get_track_by_id(
    spotify_id: Annotated[str,Path(...,description='Уникальный ID трека')],
    track_serv: track_service
) -> TrackBase:
    """
    Находит трек по ID в базе данных
    """
    return track_serv.get_track_by_Spotify_id(spotify_id)


@track.post('/',response_model=TrackCreate,dependencies=[Depends(RateLimiter(times=10, seconds=60))])
async def create_track_from_spotify_data(
    spotify_data: TrackCreate,
    track_serv: track_service
) -> TrackResponse:
    """
    Создает трек в базе данных на основе Spotify data
    """
    track_data = spotify_data.model_dump()
    return await track_serv.get_or_create_track_from_spotify(track_data)

