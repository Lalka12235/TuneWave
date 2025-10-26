from app.models import Track
from app.schemas.room_schemas import TrackInQueueResponse
from app.services.mappers.base_mapper import BaseMapper

class TrackMapper(BaseMapper):
    def to_response(self, track: Track) -> TrackInQueueResponse:
        return TrackInQueueResponse(
            id=track.id,
            name=track.name,
            duration_ms=track.duration_ms,
            preview_url=track.preview_url,
            artists=track.artists,
            album=track.album,
            spotify_id=track.spotify_id
        )