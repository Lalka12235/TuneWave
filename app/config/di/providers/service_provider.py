from dishka import Provider,Scope,provide_all

from app.application.services.user_service import UserService
from app.application.services.ban_service import BanService
from app.application.services.chat_service import ChatService
from app.application.services.favorite_track_service import FavoriteTrackService
from app.application.services.friendship_service import FriendshipService
from app.application.services.notification_service import NotificationService
from app.application.services.room_service import RoomService
from app.application.services.track_service import TrackService
from app.application.services.room_member_service import RoomMemberService
from app.application.services.room_playback_service import RoomPlaybackService
from app.application.services.room_queue_service import RoomQueueService
from app.application.services.redis_service import RedisService


class ServiceProvider(Provider):
    scope = Scope.APP

    services = provide_all(
        UserService,
        BanService,
        ChatService,
        FavoriteTrackService,
        FriendshipService,
        NotificationService,
        RoomService,
        TrackService,
        RoomMemberService,
        RoomPlaybackService,
        RoomQueueService,
        RedisService
    )


def service_provider() -> ServiceProvider:
    return ServiceProvider()