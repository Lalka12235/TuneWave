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

from app.services.user_service import UserService
from app.services.ban_service import BanService
from app.services.chat_service import ChatService
from app.services.favorite_track_service import FavoriteTrackService
from app.services.friendship_service import FriendshipService
from app.services.notification_service import NotificationService
from app.services.room_service import RoomService
from app.services.track_service import TrackService

from typing import Annotated

from app.repositories.user_repo import UserRepository
from app.repositories.ban_repo import BanRepository
from app.repositories.chat_repo import ChatRepository
from app.repositories.favorite_track_repo import FavoriteTrackRepository
from app.repositories.friendship_repo import FriendshipRepository
from app.repositories.member_room_association_repo import MemberRoomAssociationRepository
from app.repositories.notification_repo import NotificationRepository
from app.repositories.room_repo import RoomRepository
from app.repositories.track_repo import TrackRepository
from app.repositories.room_track_association_repo import RoomTrackAssociationRepository
from fastapi import Depends


def get_user_service(
    user_repo: Annotated[UserRepository, Depends(get_user_repo)],
    ban_repo: Annotated[BanRepository, Depends(get_ban_repo)],
):
    return UserService(user_repo, ban_repo)


def get_ban_service(
    ban_repo: Annotated[BanRepository, Depends(get_ban_repo)],
):
    return BanService(ban_repo)


def get_favorite_track_service(
        favorite_track_repo: Annotated[FavoriteTrackRepository,Depends(get_favorite_track_repo)],
        track_repo: Annotated[TrackRepository,Depends(get_track_repo)],
):
    return FavoriteTrackService(favorite_track_repo,track_repo)


def get_notify_service(
        notify_repo: Annotated[NotificationRepository,Depends(get_notification_repo)],
        user_repo: Annotated[UserRepository,Depends(get_user_repo)],
        room_repo: Annotated[RoomRepository,Depends(get_room_repo)],
):
    return NotificationService(notify_repo,user_repo,room_repo)


def get_track_service(
        track_repo: Annotated[TrackRepository,Depends(get_track_repo)],
):
    return TrackService(track_repo)


def get_friendship_service(
    friend_repo: Annotated[FriendshipRepository,Depends(get_friendship_repo)],
    notify_service: Annotated[NotificationService,Depends(get_notify_service)],
    user_repo: Annotated[UserRepository,Depends(get_user_repo)],
):
    return FriendshipService(friend_repo,notify_service,user_repo)

def get_room_service(
        user_repo: Annotated[UserRepository,Depends(get_user_repo)],
        ban_repo: Annotated[BanRepository, Depends(get_ban_repo)],
        notify_repo: Annotated[NotificationRepository,Depends(get_notification_repo)],
        room_track_repo: Annotated[RoomTrackAssociationRepository,Depends(get_room_track_repo)],
        room_repo: Annotated[RoomRepository,Depends(get_room_repo)],
        member_room_repo: Annotated[MemberRoomAssociationRepository,Depends(get_member_room_repo)],
        ban_service: Annotated[BanService,Depends(get_ban_service)],
        notify_service: Annotated[NotificationService,Depends(get_notify_service)],
        track_service: Annotated[TrackService,Depends(get_track_service)],
        user_service: Annotated[UserService,Depends(get_user_service)],
):
    return RoomService(
        user_repo,
        ban_repo,
        notify_repo,
        room_track_repo,
        room_repo,
        member_room_repo,
        ban_service,
        notify_service,
        track_service,
        user_service
    )

def get_chat_service(
    chat_repo: Annotated[ChatRepository, Depends(get_chat_repo)],
    room_service: Annotated[RoomService, Depends(get_room_service)],
):
    return ChatService(chat_repo, room_service)