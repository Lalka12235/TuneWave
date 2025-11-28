from dishka import Provider,Scope,provide_all,provide

from app.application.mappers.user_mapper import UserMapper
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
from app.application.services.google_service import GoogleService
from app.application.services.spotify_service import SpotifyService
from redis.asyncio import Redis

from app.domain.entity import UserEntity
from app.domain.interfaces.ban_gateway import BanGateway
from app.domain.interfaces.user_gateway import UserGateway


class ServiceProvider(Provider):
    scope = Scope.REQUEST

    @provide(scope=Scope.APP)
    def redis_service(self,client: Redis) -> RedisService:
        return RedisService(client)

    @provide
    def google_service(self,user: UserEntity,redis: RedisService) -> GoogleService:
        return GoogleService(user,redis)

    @provide
    def spotify_service(self,user: UserEntity,redis: RedisService) -> SpotifyService:
        return SpotifyService(user,redis)

    @provide
    def user_service(self, user_repo: UserGateway, ban_repo: BanGateway, user_mapper: UserMapper) -> UserService:
        return UserService(user_repo, ban_repo, user_mapper)

    services = provide_all(
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
    )