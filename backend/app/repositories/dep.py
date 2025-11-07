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

from app.repositories.abc.ban_repo import ABCBanRepository
from app.repositories.abc.chat_repo import ABCChatRepository
from app.repositories.abc.track_repo import ABCTrackRepository
from app.repositories.abc.user_repo import ABCUserRepository
from app.repositories.abc.member_room_association import ABCMemberRoomAssociationRepository
from app.repositories.abc.notification_repo import ABCNotificationRepository
from app.repositories.abc.room_repo import ABCRoomRepository
from app.repositories.abc.room_track_association_repo import ABCRoomTrackAssociationRepository
from app.repositories.abc.favorite_track_repo import ABCFavoriteTrackRepository
from app.repositories.abc.friendship_repo import ABCFriendshipRepository

from app.config.session import get_db
from fastapi import Depends
from typing import Annotated
from sqlalchemy.orm import Session


def get_user_repo(db: Annotated[Session, Depends(get_db)]) -> ABCUserRepository:
    """Get the user repository."""
    return UserRepository(db)


def get_ban_repo(db: Annotated[Session, Depends(get_db)]) -> ABCBanRepository:
    """Get the ban repository."""
    return BanRepository(db)

def get_chat_repo(db: Annotated[Session, Depends(get_db)]) -> ABCChatRepository:
    """Get the chat repository."""
    return ChatRepository(db)

def get_favorite_track_repo(db: Annotated[Session, Depends(get_db)]) -> ABCFavoriteTrackRepository:
    """Get the favorite track repository."""
    return FavoriteTrackRepository(db)

def get_friendship_repo(db: Annotated[Session, Depends(get_db)]) -> ABCFriendshipRepository:
    """Get the friendship repository."""
    return FriendshipRepository(db)

def get_member_room_repo(db: Annotated[Session, Depends(get_db)]) -> ABCMemberRoomAssociationRepository:
    """Get the member room association repository."""
    return MemberRoomAssociationRepository(db)

def get_notification_repo(db: Annotated[Session, Depends(get_db)]) -> ABCNotificationRepository:
    """Get the notification repository."""
    return NotificationRepository(db)

def get_room_repo(db: Annotated[Session, Depends(get_db)]) -> ABCRoomRepository:
    """Get the room repository."""
    return RoomRepository(db)

def get_track_repo(db: Annotated[Session, Depends(get_db)]) -> ABCTrackRepository:
    """Get the track repository."""
    return TrackRepository(db)

def get_room_track_repo(db: Annotated[Session, Depends(get_db)]) -> ABCRoomTrackAssociationRepository:
    """Get the room track association repository."""
    return RoomTrackAssociationRepository(db)