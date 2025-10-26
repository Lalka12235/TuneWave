from app.models import Room
from app.schemas.room_schemas import RoomResponse, TrackInQueueResponse
from app.services.mappers.base_mapper import BaseMapper
from app.services.mappers.user_mapper import UserMapper
from app.services.mappers.track_mapper import TrackMapper

class RoomMapper(BaseMapper):
    def __init__(self, user_mapper: UserMapper, track_mapper: TrackMapper):
        self._user_mapper = user_mapper
        self._track_mapper = track_mapper

    def to_response(self, room: Room) -> RoomResponse:
        owner_response = self._user_mapper.to_response(room.owner) if room.owner_id else None
        members_response = [
            self._user_mapper.to_response(assoc.user)
            for assoc in room.member_room
            if assoc.user
        ]
        queue_response = [
            TrackInQueueResponse(
                track=self._track_mapper.to_response(assoc.track),
                order_in_queue=assoc.order_in_queue,
                id=assoc.id,
                added_at=assoc.added_at
            )
            for assoc in sorted(room.room_track, key=lambda x: x.order_in_queue)
            if assoc.track
        ]
        
        return RoomResponse(
            id=room.id,
            name=room.name,
            owner_id=room.owner_id,
            max_members=room.max_members,
            current_members_count=room.max_members,
            is_private=room.is_private,
            created_at=room.created_at.isoformat() if room.created_at else None,
            current_track_id=room.current_track_id,
            current_track_position_ms=room.current_track_position_ms,
            is_playing=room.is_playing,
            owner=owner_response,
            members=members_response,
            queue=queue_response
        )