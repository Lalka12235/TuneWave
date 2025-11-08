from app.repositories.dep import (
    get_user_repo,
    get_ban_repo,
    get_friendship_repo,
    get_chat_repo,
    get_favorite_track_repo,
    get_member_room_repo,
    get_notification_repo,
    get_room_repo,
    get_room_track_repo,
    get_track_repo,
)

from infrastructure.redis.redis import get_redis_client

from app.services.user_service import UserService
from app.services.ban_service import BanService
from app.services.chat_service import ChatService
from app.services.favorite_track_service import FavoriteTrackService
from app.services.friendship_service import FriendshipService
from app.services.notification_service import NotificationService
from app.services.room_service import RoomService
from app.services.track_service import TrackService
from app.services.room_member_service import RoomMemberService
from app.services.room_playback_service import RoomPlaybackService
from app.services.room_queue_service import RoomQueueService
from app.services.redis_service import RedisService


from typing import Annotated

from app.repositories.user_repo import UserRepository
from app.repositories.ban_repo import BanRepository
from app.repositories.chat_repo import ChatRepository
from app.repositories.favorite_track_repo import FavoriteTrackRepository
from app.repositories.friendship_repo import FriendshipRepository
from app.repositories.member_room_association_repo import (
    MemberRoomAssociationRepository,
)
from app.repositories.notification_repo import NotificationRepository
from app.repositories.room_repo import RoomRepository
from app.repositories.track_repo import TrackRepository
from app.repositories.room_track_association_repo import RoomTrackAssociationRepository
from fastapi import Depends

from app.services.mappers.mappers import (
    get_user_mapper,
    get_ban_mapper,
    get_track_mapper,
    get_room_mapper,
    get_notification_mapper,
    get_friendship_mapper,
    get_favorite_track_mapper,
    get_message_mapper,
    get_room_member_mapper,
)
from app.services.mappers.user_mapper import UserMapper
from app.services.mappers.ban_mapper import BanMapper
from app.services.mappers.message_mapper import MessageMapper
from app.services.mappers.favorite_track_mapper import FavoriteTrackMapper
from app.services.mappers.friendship_mapper import FriendshipMapper
from app.services.mappers.notification_mapper import NotificationMapper
from app.services.mappers.room_mapper import RoomMapper
from app.services.mappers.track_mapper import TrackMapper
from app.services.mappers.mappers import RoomMemberMapper


def get_user_service(
    user_repo: Annotated[UserRepository, Depends(get_user_repo)],
    ban_repo: Annotated[BanRepository, Depends(get_ban_repo)],
    user_mapper: Annotated[UserMapper, Depends(get_user_mapper)],
):
    return UserService(user_repo, ban_repo, user_mapper)


def get_ban_service(
    ban_repo: Annotated[BanRepository, Depends(get_ban_repo)],
    ban_mapper: Annotated[BanMapper, Depends(get_ban_mapper)],
):
    return BanService(ban_repo, ban_mapper)


def get_chat_service(
    chat_repo: Annotated[ChatRepository, Depends(get_chat_repo)],
    room_repo: Annotated[RoomRepository, Depends(get_room_repo)],
    message_mapper: Annotated[MessageMapper, Depends(get_message_mapper)],
):
    return ChatService(chat_repo, room_repo, message_mapper)


def get_favorite_track_service(
    favorite_track_repo: Annotated[
        FavoriteTrackRepository, Depends(get_favorite_track_repo)
    ],
    track_repo: Annotated[TrackRepository, Depends(get_track_repo)],
    favorite_track_mapper: Annotated[
        FavoriteTrackMapper, Depends(get_favorite_track_mapper)
    ],
):
    return FavoriteTrackService(favorite_track_repo, track_repo, favorite_track_mapper)


def get_friendship_service(
    friendship_repo: Annotated[FriendshipRepository, Depends(get_friendship_repo)],
    notification_repo: Annotated[
        NotificationRepository, Depends(get_notification_repo)
    ],
    user_repo: Annotated[UserRepository, Depends(get_user_repo)],
    friendship_mapper: Annotated[FriendshipMapper, Depends(get_friendship_mapper)],
):
    return FriendshipService(
        friendship_repo, notification_repo, user_repo, friendship_mapper
    )


def get_notification_service(
    notification_repo: Annotated[
        NotificationRepository, Depends(get_notification_repo)
    ],
    user_repo: Annotated[UserRepository, Depends(get_user_repo)],
    room_repo: Annotated[RoomRepository, Depends(get_room_repo)],
    notification_mapper: Annotated[
        NotificationMapper, Depends(get_notification_mapper)
    ],
):
    return NotificationService(
        notification_repo, user_repo, room_repo, notification_mapper
    )


def get_room_service(
    room_repo: Annotated[RoomRepository, Depends(get_room_repo)],
    member_room_repo: Annotated[
        MemberRoomAssociationRepository, Depends(get_member_room_repo)
    ],
    room_mapper: Annotated[RoomMapper, Depends(get_room_mapper)],
):
    return RoomService(
        room_repo,
        member_room_repo,
        room_mapper,
    )


def get_track_service(
    track_repo: Annotated[TrackRepository, Depends(get_track_repo)],
    track_mapper: Annotated[TrackMapper, Depends(get_track_mapper)],
):
    return TrackService(track_repo, track_mapper)


def get_room_member_service(
    room_repo: Annotated[RoomRepository, Depends(get_room_repo)],
    user_repo: Annotated[UserRepository, Depends(get_user_repo)],
    member_room_repo: Annotated[
        MemberRoomAssociationRepository, Depends(get_member_room_repo)
    ],
    notification_repo: Annotated[
        NotificationRepository, Depends(get_notification_repo)
    ],
    ban_repo: Annotated[BanRepository, Depends(get_ban_repo)],
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
        user_repo: Annotated[UserRepository, Depends(get_user_repo)],
        room_track_repo: Annotated[RoomTrackAssociationRepository,Depends(get_room_track_repo)],
        room_repo: Annotated[RoomRepository, Depends(get_room_repo)],
        member_room_repo: Annotated[
        MemberRoomAssociationRepository, Depends(get_member_room_repo)
    ],
) -> RoomPlaybackService:
    return RoomPlaybackService(
        user_repo,room_track_repo,room_repo,member_room_repo
    )


def get_room_queue_service(
        room_repo: Annotated[RoomRepository, Depends(get_room_repo)],
        room_track_repo: Annotated[RoomTrackAssociationRepository,Depends(get_room_track_repo)],
        track_repo: Annotated[TrackRepository, Depends(get_track_repo)],
        member_room_repo: Annotated[
        MemberRoomAssociationRepository, Depends(get_member_room_repo)
    ],
) -> RoomQueueService:
    return RoomQueueService(
        room_repo,room_track_repo,track_repo,member_room_repo
    )

def get_redis_service(
        redis_client: Annotated[RedisService,Depends(get_redis_client)],
) -> RedisService:
    return RedisService(redis_client)