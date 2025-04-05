from fastapi import APIRouter
from app.services.track_services import TrackServices
from app.schemas.track_schema import TrackSchema, GetTrackSchema, DeleteTrackSchema, UpdateTrackSchema


track = APIRouter(
    tags=['Track']
)


@track.get('/track/{track.artist}/{track.title}/get')
async def get_track(track: GetTrackSchema):
    return TrackServices.get_track(track)


@track.post('/track/{track.artist}/{track.title}/create')
async def create_track(username: str,track: TrackSchema):
    return TrackServices.create_track(username,track)


@track.put('/track/{track.artist}/{track.title}/update')
async def update_track(upd_track: UpdateTrackSchema):
    return TrackServices.update_track(upd_track)


@track.delete('/track/{track.artist}/{track.title}/delet')
async def delete_track(username: str, del_track: DeleteTrackSchema):
    return TrackServices.delete_track(username,del_track)