from fastapi import Depends
from app.application.mappers.user_mapper import UserMapper
from app.application.mappers.track_mapper import TrackMapper
from app.application.mappers.room_mapper import RoomMapper
from app.application.mappers.ban_mapper import BanMapper
from app.application.mappers.notification_mapper import NotificationMapper
from app.application.mappers.friendship_mapper import FriendshipMapper
from app.application.mappers.message_mapper import MessageMapper
from app.application.mappers.room_member_mapper import RoomMemberMapper
from app.application.mappers.favorite_track_mapper import FavoriteTrackMapper


def get_user_mapper():
    return UserMapper()


def get_track_mapper():
    return TrackMapper()


def get_room_mapper(
    user_mapper: UserMapper = Depends(get_user_mapper),
    track_mapper: TrackMapper = Depends(get_track_mapper),
):
    return RoomMapper(user_mapper, track_mapper)


def get_ban_mapper(user_mapper: UserMapper = Depends(get_user_mapper)):
    return BanMapper(user_mapper)


def get_notification_mapper(user_mapper: UserMapper = Depends(get_user_mapper)):
    return NotificationMapper(user_mapper)


def get_friendship_mapper(user_mapper: UserMapper = Depends(get_user_mapper)):
    return FriendshipMapper(user_mapper)


def get_favorite_track_mapper(
    user_mapper: UserMapper = Depends(get_user_mapper),
    track_mapper: TrackMapper = Depends(get_track_mapper),
):
    return FavoriteTrackMapper(user_mapper, track_mapper)


def get_message_mapper(user_mapper: UserMapper = Depends(get_user_mapper)):
    return MessageMapper(user_mapper)


def get_room_member_mapper(user_mapper: UserMapper = Depends(get_user_mapper)):
    return RoomMemberMapper(user_mapper)