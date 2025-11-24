from dishka import Provider,Scope,provide_all

from app.application.mappers.user_mapper import UserMapper
from app.application.mappers.ban_mapper import BanMapper
from app.application.mappers.message_mapper import MessageMapper
from app.application.mappers.favorite_track_mapper import FavoriteTrackMapper
from app.application.mappers.friendship_mapper import FriendshipMapper
from app.application.mappers.notification_mapper import NotificationMapper
from app.application.mappers.room_mapper import RoomMapper
from app.application.mappers.track_mapper import TrackMapper
from app.application.mappers.mappers import RoomMemberMapper


class MapperProvider(Provider):
    scope = Scope.APP

    mappers = provide_all(
        UserMapper,
        BanMapper,
        MessageMapper,
        FavoriteTrackMapper,
        FriendshipMapper,
        NotificationMapper,
        RoomMapper,
        TrackMapper,
        RoomMemberMapper,
    )