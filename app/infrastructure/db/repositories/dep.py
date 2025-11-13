from app.infrastructure.db.repositories.user_repo import SQLalchemyUserRepository
from app.infrastructure.db.repositories.ban_repo import SQLalchemyBanRepository
from app.infrastructure.db.repositories.chat_repo import SQLalchemyChatRepository
from app.infrastructure.db.repositories.favorite_track_repo import SQLalchemyFavoriteTrackRepository
from app.infrastructure.db.repositories.friendship_repo import SQLalchemyFriendshipRepository
from app.infrastructure.db.repositories.member_room_association_repo import SQLalchemyMemberRoomAssociationRepository
from app.infrastructure.db.repositories.notification_repo import SQLalchemyNotificationRepository
from app.infrastructure.db.repositories.room_repo import SQLalchemyRoomRepository
from app.infrastructure.db.repositories.track_repo import SQLalchemyTrackRepository
from app.infrastructure.db.repositories.room_track_association_repo import SQLalchemyRoomTrackAssociationRepository

from app.domain.interfaces.ban_repo import BanRepository
from app.domain.interfaces.chat_repo import ChatRepository
from app.domain.interfaces.track_repo import TrackRepository
from app.domain.interfaces.user_repo import UserRepository
from app.domain.interfaces.member_room_association import MemberRoomAssociationRepository
from app.domain.interfaces.notification_repo import NotificationRepository
from app.domain.interfaces.room_repo import RoomRepository
from app.domain.interfaces.room_track_association_repo import RoomTrackAssociationRepository
from app.domain.interfaces.favorite_track_repo import FavoriteTrackRepository
from app.domain.interfaces.friendship_repo import FriendshipRepository

from app.config.session import get_db
from fastapi import Depends
from typing import Annotated
from sqlalchemy.orm import Session


def get_user_repo(db: Annotated[Session, Depends(get_db)]) -> UserRepository:
    """Get the user repository."""
    return SQLalchemyUserRepository(db)


def get_ban_repo(db: Annotated[Session, Depends(get_db)]) -> BanRepository:
    """Get the ban repository."""
    return SQLalchemyBanRepository(db)

def get_chat_repo(db: Annotated[Session, Depends(get_db)]) -> ChatRepository:
    """Get the chat repository."""
    return SQLalchemyChatRepository(db)

def get_favorite_track_repo(db: Annotated[Session, Depends(get_db)]) -> FavoriteTrackRepository:
    """Get the favorite track repository."""
    return SQLalchemyFavoriteTrackRepository(db)

def get_friendship_repo(db: Annotated[Session, Depends(get_db)]) -> FriendshipRepository:
    """Get the friendship repository."""
    return SQLalchemyFriendshipRepository(db)

def get_member_room_repo(db: Annotated[Session, Depends(get_db)]) -> MemberRoomAssociationRepository:
    """Get the member room association repository."""
    return SQLalchemyMemberRoomAssociationRepository(db)

def get_notification_repo(db: Annotated[Session, Depends(get_db)]) -> NotificationRepository:
    """Get the notification repository."""
    return SQLalchemyNotificationRepository(db)

def get_room_repo(db: Annotated[Session, Depends(get_db)]) -> RoomRepository:
    """Get the room repository."""
    return SQLalchemyRoomRepository(db)

def get_track_repo(db: Annotated[Session, Depends(get_db)]) -> TrackRepository:
    """Get the track repository."""
    return SQLalchemyTrackRepository(db)

def get_room_track_repo(db: Annotated[Session, Depends(get_db)]) -> RoomTrackAssociationRepository:
    """Get the room track association repository."""
    return SQLalchemyRoomTrackAssociationRepository(db)