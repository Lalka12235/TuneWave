from app.domain.entity import TrackEntity,RoomTrackAssociationEntity
from app.presentation.schemas.room_schemas import TrackInQueueResponse
from app.presentation.schemas.track_schemas import TrackResponse

class TrackMapper:

    def to_response_track(self,track: TrackEntity)  -> TrackResponse:
        return TrackResponse(
            id=track.id,
            spotify_id=track.spotify_id,
            spotify_uri=track.spotify_uri,
            title=track.title,
            artist_names=track.artist_names,
            album_name=track.album_name,
            album_cover_url=track.album_cover_url,
            duration_ms=track.duration_ms,
            is_playable=track.is_playable,
            spotify_track_url=track.spotify_track_url,
            last_synced_at=track.last_synced_at,
            created_at=track.created_at,
        )

    def to_response_in_queue(self, track: TrackEntity,room_track: RoomTrackAssociationEntity) -> TrackInQueueResponse:
        return TrackInQueueResponse(
            id=room_track.id,
            track=self.to_response_track(track),
            order_in_queue=room_track.order_in_queue,
            added_at=room_track.added_at,
        )