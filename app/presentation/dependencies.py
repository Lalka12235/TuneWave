from typing import Annotated
from fastapi import Depends
from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker
from redis.asyncio import Redis

from app.domain.entity import UserEntity

from app.application.services.avatar_storage_service import AvatarStorageService
# 1. КОНФИГУРАЦИЯ И СЕССИИ
from app.config.session import get_engine,get_sessionmaker,get_session
from app.infrastructure.db.gateway.avatar_storage_gateway import LocalAvatarStorageGateway
from app.infrastructure.redis.redis import get_redis_client

# 2. ИНТЕРФЕЙСЫ (DOMAIN/APPLICATION)
from app.domain.interfaces.user_gateway import UserGateway
from app.domain.interfaces.ban_gateway import BanGateway
from app.domain.interfaces.chat_gateway import ChatGateway
from app.domain.interfaces.favorite_track_gateway import FavoriteTrackGateway
from app.domain.interfaces.friendship_gateway import FriendshipGateway
from app.domain.interfaces.member_room_association import MemberRoomAssociationGateway
from app.domain.interfaces.notification_gateway import NotificationGateway
from app.domain.interfaces.room_gateway import RoomGateway
from app.domain.interfaces.track_gateway import TrackGateway
from app.domain.interfaces.room_track_association_gateway import RoomTrackAssociationGateway
from app.domain.interfaces.avatar_storage_gateway import AvatarStorageGateway

# 3. ИМПЛЕМЕНТАЦИИ (INFRASTRUCTURE)
from app.infrastructure.db.gateway.user_gateway import SAUserGateway
from app.infrastructure.db.gateway.ban_gateway import SABanGateway
from app.infrastructure.db.gateway.chat_gateway import SAChatGateway
from app.infrastructure.db.gateway.favorite_track_gateway import SAFavoriteTrackGateway
from app.infrastructure.db.gateway.friendship_gateway import SAFriendshipGateway
from app.infrastructure.db.gateway.member_room_association_gateway import SAMemberRoomAssociationGateway
from app.infrastructure.db.gateway.notification_gateway import SANotificationGateway
from app.infrastructure.db.gateway.room_gateway import SARoomGateway
from app.infrastructure.db.gateway.track_gateway import SATrackGateway
from app.infrastructure.db.gateway.room_track_association_gateway import SARoomTrackAssociationGateway

# 4. МАППЕРЫ (APPLICATION)
from app.application.mappers.user_mapper import UserMapper
from app.application.mappers.ban_mapper import BanMapper
from app.application.mappers.favorite_track_mapper import FavoriteTrackMapper
from app.application.mappers.friendship_mapper import FriendshipMapper
from app.application.mappers.notification_mapper import NotificationMapper
from app.application.mappers.room_mapper import RoomMapper
from app.application.mappers.track_mapper import TrackMapper
from app.application.mappers.message_mapper import MessageMapper
from app.application.mappers.room_member_mapper import RoomMemberMapper

# 5. СЕРВИСЫ (APPLICATION)
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
from app.presentation.auth.auth import AuthService,get_current_user
from app.application.services.google_service import GoogleService
from app.application.services.spotify_service import SpotifyService


# --- БАЗОВЫЕ ЗАВИСИМОСТИ ---


def get_engine_dep() -> Engine:
    return get_engine()

def get_session_dep(engine: Annotated[Engine,Depends(get_engine_dep)]):
    return get_sessionmaker(engine)

def get_db(session: Annotated[sessionmaker[Session],Depends(get_session_dep)]):
    return get_session(session)

async def get_redis() -> Redis:
    return await get_redis_client()

# --- GATEWAYS (РЕПОЗИТОРИИ) ---

def get_user_repo(db: Session = Depends(get_db)) -> UserGateway:
    return SAUserGateway(db)

def get_ban_repo(db: Session = Depends(get_db)) -> BanGateway:
    return SABanGateway(db)

def get_chat_repo(db: Session = Depends(get_db)) -> ChatGateway:
    return SAChatGateway(db)

def get_favorite_track_repo(db: Session = Depends(get_db)) -> FavoriteTrackGateway:
    return SAFavoriteTrackGateway(db)

def get_friendship_repo(db: Session = Depends(get_db)) -> FriendshipGateway:
    return SAFriendshipGateway(db)

def get_member_room_association_repo(db: Session = Depends(get_db)) -> MemberRoomAssociationGateway:
    return SAMemberRoomAssociationGateway(db)

def get_notification_repo(db: Session = Depends(get_db)) -> NotificationGateway:
    return SANotificationGateway(db)

def get_room_repo(db: Session = Depends(get_db)) -> RoomGateway:
    return SARoomGateway(db)

def get_track_repo(db: Session = Depends(get_db)) -> TrackGateway:
    return SATrackGateway(db)

def get_room_track_association_repo(db: Session = Depends(get_db)) -> RoomTrackAssociationGateway:
    return SARoomTrackAssociationGateway(db)

def get_avatar_storage_repo() -> AvatarStorageGateway:
    return LocalAvatarStorageGateway()


# --- МАППЕРЫ ---

def get_user_mapper() -> UserMapper:
    return UserMapper()

def get_ban_mapper(user_mapper: Annotated[UserMapper,Depends(get_user_mapper)]) -> BanMapper:
    return BanMapper(user_mapper)

def get_track_mapper() -> TrackMapper:
    return TrackMapper()

def get_favorite_track_mapper(
        user_mapper: Annotated[UserMapper,Depends(get_user_mapper)],
        track_mapper: Annotated[TrackMapper,Depends(get_track_mapper)],
) -> FavoriteTrackMapper:
    return FavoriteTrackMapper(user_mapper,track_mapper)

def get_friendship_mapper(user_mapper: Annotated[UserMapper,Depends(get_user_mapper)]) -> FriendshipMapper:
    return FriendshipMapper(user_mapper)

def get_notification_mapper(user_mapper: Annotated[UserMapper,Depends(get_user_mapper)]) -> NotificationMapper:
    return NotificationMapper(user_mapper)

def get_room_mapper(
        user_mapper: Annotated[UserMapper,Depends(get_user_mapper)],
        track_mapper: Annotated[TrackMapper,Depends(get_track_mapper)]
) -> RoomMapper:
    return RoomMapper(user_mapper,track_mapper)

def get_message_mapper(user_mapper: Annotated[UserMapper,Depends(get_user_mapper)],) -> MessageMapper:
    return MessageMapper(user_mapper)

def get_room_member_mapper(
        user_mapper: Annotated[UserMapper,Depends(get_user_mapper)],
) -> RoomMemberMapper:
    return RoomMemberMapper(user_mapper)


# --- СЕРВИСЫ ---

def get_redis_service(redis: Redis = Depends(get_redis)) -> RedisService:
    return RedisService(redis)

def get_user_service(
    user_repo: Annotated[UserGateway,Depends(get_user_repo)],
    ban_repo: Annotated[BanGateway,Depends(get_ban_repo)],
    user_mapper: Annotated[UserMapper,Depends(get_user_mapper)]
) -> UserService:
    return UserService(user_repo, ban_repo, user_mapper)

def get_ban_service(
    ban_repo: Annotated[BanGateway,Depends(get_ban_repo)],
    ban_mapper: Annotated[BanMapper, Depends(get_ban_mapper)]
) -> BanService:
    return BanService(ban_repo, ban_mapper)

def get_chat_service(
    chat_repo: Annotated[ChatGateway,Depends(get_chat_repo)],
    room_repo: Annotated[RoomGateway,Depends(get_room_repo)],
    chat_mapper: Annotated[MessageMapper,Depends(get_message_mapper)],
    member_room: Annotated[MemberRoomAssociationGateway,Depends(get_member_room_association_repo)],
) -> ChatService:
    return ChatService(chat_repo,room_repo, chat_mapper,member_room)

def get_favorite_track_service(
    favorite_track_repo: Annotated[FavoriteTrackGateway,Depends(get_favorite_track_repo)],
    track_repo: Annotated[TrackGateway,Depends(get_track_repo)],
    favorite_track_mapper: Annotated[FavoriteTrackMapper,Depends(get_favorite_track_mapper)],
) -> FavoriteTrackService:
    return FavoriteTrackService(favorite_track_repo,track_repo, favorite_track_mapper)

def get_friendship_service(
    friendship_repo: Annotated[FriendshipGateway, Depends(get_friendship_repo)],
    notification_repo: Annotated[NotificationGateway, Depends(get_notification_repo)],
    user_repo: Annotated[UserGateway, Depends(get_user_repo)],
    friendship_mapper: Annotated[FriendshipMapper, Depends(get_friendship_mapper)]
) -> FriendshipService:
    return FriendshipService(friendship_repo, notification_repo, user_repo, friendship_mapper)

def get_notification_service(
    notification_repo: Annotated[NotificationGateway, Depends(get_notification_repo)],
    user_repo: Annotated[UserGateway, Depends(get_user_repo)],
    room_repo: Annotated[RoomGateway, Depends(get_room_repo)],
    notification_mapper: Annotated[NotificationMapper, Depends(get_notification_mapper)]
) -> NotificationService:
    return NotificationService(notification_repo, user_repo, room_repo, notification_mapper)

def get_room_service(
    room_repo: Annotated[RoomGateway, Depends(get_room_repo)],
    member_room_repo: Annotated[MemberRoomAssociationGateway, Depends(get_member_room_association_repo)],
    room_mapper: Annotated[RoomMapper, Depends(get_room_mapper)]
) -> RoomService:
    return RoomService(room_repo, member_room_repo, room_mapper)

def get_track_service(
    track_repo: Annotated[TrackGateway, Depends(get_track_repo)],
    track_mapper: Annotated[TrackMapper, Depends(get_track_mapper)]
) -> TrackService:
    return TrackService(track_repo, track_mapper)

def get_room_member_service(
    room_repo: Annotated[RoomGateway, Depends(get_room_repo)],
    user_repo: Annotated[UserGateway, Depends(get_user_repo)],
    member_room_repo: Annotated[MemberRoomAssociationGateway, Depends(get_member_room_association_repo)],
    ban_repo: Annotated[BanGateway, Depends(get_ban_repo)],
    notify_repo: Annotated[NotificationGateway, Depends(get_notification_repo)],
    room_mapper: Annotated[RoomMapper, Depends(get_room_mapper)],
    user_mapper: Annotated[UserMapper, Depends(get_user_mapper)],
    ban_mapper: Annotated[BanMapper, Depends(get_ban_mapper)],
    room_member_mapper: Annotated[RoomMemberMapper, Depends(get_room_member_mapper)],
    notify_mapper: Annotated[NotificationMapper, Depends(get_notification_mapper)]
) -> RoomMemberService:
    return RoomMemberService(
        room_repo, user_repo, member_room_repo, ban_repo, notify_repo,
        room_mapper, user_mapper, ban_mapper, room_member_mapper, notify_mapper
    )

def get_room_playback_service(
    user_repo: Annotated[UserGateway, Depends(get_user_repo)],
    room_track_repo: Annotated[RoomTrackAssociationGateway, Depends(get_room_track_association_repo)],
    room_repo: Annotated[RoomGateway, Depends(get_room_repo)],
    member_room_repo: Annotated[MemberRoomAssociationGateway, Depends(get_member_room_association_repo)],
) -> RoomPlaybackService:
    return RoomPlaybackService(
        user_repo, room_track_repo, room_repo, member_room_repo
    )

def get_room_queue_service(
    room_repo: Annotated[RoomGateway, Depends(get_room_repo)],
    room_track_repo: Annotated[RoomTrackAssociationGateway, Depends(get_room_track_association_repo)],
    track_repo: Annotated[TrackGateway, Depends(get_track_repo)],
    member_room_repo: Annotated[MemberRoomAssociationGateway, Depends(get_member_room_association_repo)],
) -> RoomQueueService:
    return RoomQueueService(
        room_repo, room_track_repo, track_repo, member_room_repo
    )

def get_avatar_storage_service(
        avatar_storage: Annotated[AvatarStorageGateway, Depends(get_avatar_storage_repo)],
        user_repo: Annotated[UserGateway, Depends(get_user_repo)],
        user_mapper: Annotated[UserMapper, Depends(get_user_mapper)]
) -> AvatarStorageService:
    return AvatarStorageService(avatar_storage, user_repo, user_mapper)


def get_auth_service(
    user_repo: Annotated[UserGateway, Depends(get_user_repo)],
    ban_repo: Annotated[BanGateway, Depends(get_ban_repo)],
    user_mapper: Annotated[UserMapper, Depends(get_user_mapper)],
    redis_service: Annotated[RedisService, Depends(get_redis_service)],
) -> AuthService:
    return AuthService(user_repo, ban_repo, user_mapper, redis_service)

def get_google_service(
    user: Annotated[UserEntity, Depends(get_current_user)],
    redis: Annotated[RedisService, Depends(get_redis_service)],
) -> GoogleService:
    return GoogleService(user, redis)

def get_spotify_service(
    user: Annotated[UserEntity, Depends(get_current_user)],
    redis: Annotated[RedisService, Depends(get_redis_service)],
) -> SpotifyService:
    return SpotifyService(user, redis)
