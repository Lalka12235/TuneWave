from typing import Annotated

from fastapi import Depends

from app.infrastructure.redis.redis import get_redis_client
from app.infrastructure.db.repositories.ban_repo import SQLalchemyBanRepository
from app.infrastructure.db.repositories.chat_repo import SQLalchemyChatRepository
from app.infrastructure.db.repositories.dep import (
    get_ban_repo,
    get_chat_repo,
    get_favorite_track_repo,
    get_friendship_repo,
    get_member_room_repo,
    get_notification_repo,
    get_room_repo,
    get_room_track_repo,
    get_track_repo,
    get_user_repo,
)
from app.infrastructure.db.repositories.favorite_track_repo import SQLalchemyFavoriteTrackRepository
from app.infrastructure.db.repositories.friendship_repo import SQLalchemyFriendshipRepository
from app.infrastructure.db.repositories.member_room_association_repo import (
    SQLalchemyMemberRoomAssociationRepository,
)
from app.infrastructure.db.repositories.notification_repo import SQLalchemyNotificationRepository
from app.infrastructure.db.repositories.room_repo import SQLalchemyRoomRepository
from app.infrastructure.db.repositories.room_track_association_repo import (
    SQLalchemyRoomTrackAssociationRepository,
)
from app.infrastructure.db.repositories.track_repo import SQLalchemyTrackRepository
from app.infrastructure.db.repositories.user_repo import SQLalchemyUserRepository
from app.application.mappers.ban_mapper import BanMapper
from app.application.mappers.favorite_track_mapper import FavoriteTrackMapper
from app.application.mappers.friendship_mapper import FriendshipMapper
from app.application.mappers.mappers import (
    RoomMemberMapper,
    get_ban_mapper,
    get_favorite_track_mapper,
    get_friendship_mapper,
    get_message_mapper,
    get_notification_mapper,
    get_room_mapper,
    get_room_member_mapper,
    get_track_mapper,
    get_user_mapper,
)
from app.application.mappers.message_mapper import MessageMapper
from app.application.mappers.notification_mapper import NotificationMapper
from app.application.mappers.room_mapper import RoomMapper
from app.application.mappers.track_mapper import TrackMapper
from app.application.mappers.user_mapper import UserMapper
from app.application.services.notification_service import NotificationService
from app.application.services.redis_service import RedisService
from app.application.services.room_member_service import RoomMemberService
from app.application.services.room_playback_service import RoomPlaybackService
from app.application.services.room_queue_service import RoomQueueService
from app.application.services.room_service import RoomService
from app.application.services.track_service import TrackService
from app.application.services.user_service import UserService
from app.application.services.ban_service import BanService
from app.application.services.chat_service import ChatService
from app.application.services.favorite_track_service import FavoriteTrackService
from app.application.services.friendship_service import FriendshipService


def get_user_service(
    user_repo: Annotated[SQLalchemyUserRepository, Depends(get_user_repo)],
    ban_repo: Annotated[SQLalchemyBanRepository, Depends(get_ban_repo)],
    user_mapper: Annotated[UserMapper, Depends(get_user_mapper)],
):
    return UserService(user_repo, ban_repo, user_mapper)


def get_ban_service(
    ban_repo: Annotated[SQLalchemyBanRepository, Depends(get_ban_repo)],
    ban_mapper: Annotated[BanMapper, Depends(get_ban_mapper)],
):
    return BanService(ban_repo, ban_mapper)


def get_chat_service(
    chat_repo: Annotated[SQLalchemyChatRepository, Depends(get_chat_repo)],
    room_repo: Annotated[SQLalchemyRoomRepository, Depends(get_room_repo)],
    message_mapper: Annotated[MessageMapper, Depends(get_message_mapper)],
):
    return ChatService(chat_repo, room_repo, message_mapper)


def get_favorite_track_service(
    favorite_track_repo: Annotated[
        SQLalchemyFavoriteTrackRepository, Depends(get_favorite_track_repo)
    ],
    track_repo: Annotated[SQLalchemyTrackRepository, Depends(get_track_repo)],
    favorite_track_mapper: Annotated[
        FavoriteTrackMapper, Depends(get_favorite_track_mapper)
    ],
):
    return FavoriteTrackService(favorite_track_repo, track_repo, favorite_track_mapper)


def get_friendship_service(
    friendship_repo: Annotated[
        SQLalchemyFriendshipRepository, Depends(get_friendship_repo)
    ],
    notification_repo: Annotated[
        SQLalchemyNotificationRepository, Depends(get_notification_repo)
    ],
    user_repo: Annotated[SQLalchemyUserRepository, Depends(get_user_repo)],
    friendship_mapper: Annotated[FriendshipMapper, Depends(get_friendship_mapper)],
):
    return FriendshipService(
        friendship_repo, notification_repo, user_repo, friendship_mapper
    )


def get_notification_service(
    notification_repo: Annotated[
        SQLalchemyNotificationRepository, Depends(get_notification_repo)
    ],
    user_repo: Annotated[SQLalchemyUserRepository, Depends(get_user_repo)],
    room_repo: Annotated[SQLalchemyRoomRepository, Depends(get_room_repo)],
    notification_mapper: Annotated[
        NotificationMapper, Depends(get_notification_mapper)
    ],
):
    return NotificationService(
        notification_repo, user_repo, room_repo, notification_mapper
    )


def get_room_service(
    room_repo: Annotated[SQLalchemyRoomRepository, Depends(get_room_repo)],
    member_room_repo: Annotated[
        SQLalchemyMemberRoomAssociationRepository, Depends(get_member_room_repo)
    ],
    room_mapper: Annotated[RoomMapper, Depends(get_room_mapper)],
):
    return RoomService(
        room_repo,
        member_room_repo,
        room_mapper,
    )


def get_track_service(
    track_repo: Annotated[SQLalchemyTrackRepository, Depends(get_track_repo)],
    track_mapper: Annotated[TrackMapper, Depends(get_track_mapper)],
):
    return TrackService(track_repo, track_mapper)


def get_room_member_service(
    room_repo: Annotated[SQLalchemyRoomRepository, Depends(get_room_repo)],
    user_repo: Annotated[SQLalchemyUserRepository, Depends(get_user_repo)],
    member_room_repo: Annotated[
        SQLalchemyMemberRoomAssociationRepository, Depends(get_member_room_repo)
    ],
    notification_repo: Annotated[
        SQLalchemyNotificationRepository, Depends(get_notification_repo)
    ],
    ban_repo: Annotated[SQLalchemyBanRepository, Depends(get_ban_repo)],
    room_mapper: Annotated[RoomMapper, Depends(get_room_mapper)],
    user_mapper: Annotated[UserMapper, Depends(get_user_mapper)],
    ban_mapper: Annotated[BanMapper, Depends(get_ban_mapper)],
    room_member_mapper: Annotated[RoomMemberMapper, Depends(get_room_member_mapper)],
) -> RoomMemberService:
    return RoomMemberService(
        room_repo,
        user_repo,
        member_room_repo,
        notification_repo,
        ban_repo,
        room_mapper,
        user_mapper,
        ban_mapper,
        room_member_mapper,
    )


def get_room_playback_service(
    user_repo: Annotated[SQLalchemyUserRepository, Depends(get_user_repo)],
    room_track_repo: Annotated[
        SQLalchemyRoomTrackAssociationRepository, Depends(get_room_track_repo)
    ],
    room_repo: Annotated[SQLalchemyRoomRepository, Depends(get_room_repo)],
    member_room_repo: Annotated[
        SQLalchemyMemberRoomAssociationRepository, Depends(get_member_room_repo)
    ],
) -> RoomPlaybackService:
    return RoomPlaybackService(user_repo, room_track_repo, room_repo, member_room_repo)


def get_room_queue_service(
    room_repo: Annotated[SQLalchemyRoomRepository, Depends(get_room_repo)],
    room_track_repo: Annotated[
        SQLalchemyRoomTrackAssociationRepository, Depends(get_room_track_repo)
    ],
    track_repo: Annotated[SQLalchemyTrackRepository, Depends(get_track_repo)],
    member_room_repo: Annotated[
        SQLalchemyMemberRoomAssociationRepository, Depends(get_member_room_repo)
    ],
) -> RoomQueueService:
    return RoomQueueService(room_repo, room_track_repo, track_repo, member_room_repo)


def get_redis_service(
    redis_client: Annotated[RedisService, Depends(get_redis_client)],
) -> RedisService:
    return RedisService(redis_client)
