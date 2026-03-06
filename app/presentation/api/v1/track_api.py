from typing import Annotated

from fastapi import APIRouter,Path


from app.presentation.schemas.track_schemas import TrackBase, TrackCreate, TrackResponse
from dishka.integrations.fastapi import DishkaRoute,FromDishka
from app.application.commands.track import ReadTrack,CreateTrack,DeleteTrack


track = APIRouter(
    tags=['Track'],
    prefix='/track',
    route_class=DishkaRoute
)


@track.get('/{spotify_id}',response_model=TrackBase)
async def get_track_by_id(
    spotify_id: Annotated[str,Path(...,description='Уникальный ID трека')],
    interactor: FromDishka[ReadTrack],
) -> TrackBase:
    """
    Находит трек по ID в базе данных
    """
    return interactor.get_track_by_Spotify_id(spotify_id)


@track.post('/',response_model=TrackCreate)
async def create_track_from_spotify_data(
    spotify_data: TrackCreate,
    interactor: FromDishka[CreateTrack],
) -> TrackResponse:
    """
    Создает трек в базе данных на основе Spotify data
    """
    track_data = spotify_data.model_dump()
    return await interactor.get_or_create_track_from_spotify(track_data)