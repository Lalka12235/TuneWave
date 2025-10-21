from app.schemas.ban_schemas import BanResponse
from app.schemas.room_schemas import RoomMemberResponse, TrackInQueueResponse, RoomResponse
from app.schemas.user_schemas import UserResponse
from app.models import Ban,Track,User,Member_room_association, Room



def map_ban_to_response(ban: Ban) -> BanResponse:
    return BanResponse.model_validate(ban)

def map_track_to_response(track: Track) -> TrackInQueueResponse:
    return TrackInQueueResponse.model_validate(track)

def map_user_to_response(user: User) -> UserResponse:
    return UserResponse.model_validate(user)

def map_member_to_response(member: Member_room_association) -> RoomMemberResponse:
        """
        Вспомогательный метод для маппинга Member_room_association (включая загруженный User)
        в Pydantic RoomMemberResponse.
        """
        return RoomMemberResponse.model_validate(member)


def map_room_to_response(room: Room) -> RoomResponse:
        """
        Преобразует объект модели Room в Pydantic-схему RoomResponse,
        включая информацию об участниках и очереди треков.
        """
        owner_response = map_user_to_response(room.owner) if room.owner_id else None
        
        members_response = []
        if room.member_room:
            for member_association in room.member_room:
                if member_association.user:
                    members_response.append(map_user_to_response(member_association.user))

        queue_response = []
        if room.room_track:
            sorted_associations = sorted(room.room_track, key=lambda x: x.order_in_queue)
            for assoc in sorted_associations:
                if assoc.track:
                    queue_response.append(
                        TrackInQueueResponse(
                            track=map_track_to_response(assoc.track),
                            order_in_queue=assoc.order_in_queue,
                            id=assoc.id,
                            added_at=assoc.added_at,
                        )
                    )

        room_data = RoomResponse(
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
        return room_data