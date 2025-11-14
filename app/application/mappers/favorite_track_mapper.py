from app.domain.entity import FavoriteTrackEntity
from app.presentation.schemas.favorite_track_schemas import FavoriteTrackResponse
from app.application.mappers.track_mapper import TrackMapper
from app.application.mappers.user_mapper import UserMapper

class FavoriteTrackMapper:
    def __init__(self, user_mapper: UserMapper, track_mapper: TrackMapper):
        self._user_mapper = user_mapper
        self._track_mapper = track_mapper

    def to_response(self, favorite_track: FavoriteTrackEntity) -> FavoriteTrackResponse:
        return FavoriteTrackResponse(

        )