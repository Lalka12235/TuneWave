from fastapi import APIRouter
from app.services.track_services import TrackServices
from app.schemas.track_schema import TrackSchema, GetTrackSchema, DeleteTrackSchema, UpdateTrackSchema


track = APIRouter(
    tags=['Track']
)


@track.get('/track/{artist}/{title}/get')
async def get_track(artist: str, title: str):
    track = GetTrackSchema(artist=artist, title=title)
    return TrackServices.get_track(track)


@track.post('/track/{track}/{track}/create')
async def create_track(username: str,artist: str, title: str):
    track = GetTrackSchema(artist=artist, title=title)
    return TrackServices.create_track(username,track)


@track.put('/track/{track}/{track}/update')
async def update_track(artist: str, title: str):
    track = UpdateTrackSchema(artist=artist, title=title)
    return TrackServices.update_track(track)


@track.delete('/track/{track}/{track}/delete')
async def delete_track(username: str, artist: str, title: str):
    track = DeleteTrackSchema(artist=artist, title=title)
    return TrackServices.delete_track(username,track)