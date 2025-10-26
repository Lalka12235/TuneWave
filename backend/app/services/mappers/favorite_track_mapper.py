from app.models import FavoriteTrack
from app.schemas.favorite_track_schemas import FavoriteTrackResponse
from app.services.mappers.base_mapper import BaseMapper
from app.services.mappers.track_mapper import TrackMapper
from app.services.mappers.user_mapper import UserMapper

class FavoriteTrackMapper(BaseMapper):
    def __init__(self, user_mapper: UserMapper, track_mapper: TrackMapper):
        self._user_mapper = user_mapper
        self._track_mapper = track_mapper

    def to_response(self, favorite_track: FavoriteTrack) -> FavoriteTrackResponse:
        return FavoriteTrackResponse(
            id=favorite_track.id,
            user=self._user_mapper.to_response(favorite_track.user),
            track=self._track_mapper.to_response(favorite_track.track),
            added_at=favorite_track.added_at
        )