from app.models import Room, User, Track, Ban, Notification, Friendship, FavoriteTrack, Message,Member_room_association
from app.schemas.room_schemas import RoomResponse, TrackInQueueResponse
from app.schemas.user_schemas import UserResponse
from app.schemas.ban_schemas import BanResponse
from app.schemas.notification_schemas import NotificationResponse
from app.schemas.friendship_schemas import FriendshipResponse
from app.schemas.favorite_track_schemas import FavoriteTrackResponse
from app.schemas.message_schemas import MessageResponse
from app.schemas.room_member_schemas import RoomMemberResponse

class RoomMapper:
    @staticmethod
    def to_response(room: Room) -> RoomResponse:
        owner_response = UserMapper.to_response(room.owner) if room.owner_id else None
        members_response = [
            UserMapper.to_response(assoc.user)
            for assoc in room.member_room
            if assoc.user
        ]
        queue_response = [
            TrackInQueueResponse(
                track=TrackMapper.to_response(assoc.track),
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

class UserMapper:
    @staticmethod
    def to_response(user: User) -> UserResponse:
        return UserResponse.model_validate(user)

class TrackMapper:
    @staticmethod
    def to_response(track: Track) -> TrackInQueueResponse:
        return TrackInQueueResponse.model_validate(track)

class BanMapper:
    @staticmethod
    def to_response(ban: Ban) -> BanResponse:
        return BanResponse.model_validate(ban)

class NotificationMapper:
    @staticmethod
    def to_response(notification: Notification) -> NotificationResponse:
        return NotificationResponse.model_validate(notification)

class FriendshipMapper:
    @staticmethod
    def to_response(friendship: Friendship) -> FriendshipResponse:
        return FriendshipResponse.model_validate(friendship)

class FavoriteTrackMapper:
    @staticmethod
    def to_response(favorite_track: FavoriteTrack) -> FavoriteTrackResponse:
        return FavoriteTrackResponse.model_validate(favorite_track)

class MessageMapper:
    @staticmethod
    def to_response(message: Message) -> MessageResponse:
        return MessageResponse.model_validate(message)
    

class RoomMemberMapper:
    @staticmethod
    def to_response(member: Member_room_association) -> RoomMemberResponse:
        return RoomMemberResponse.model_validate(member)