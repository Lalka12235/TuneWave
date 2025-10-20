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

from app.config.session import get_db
from fastapi import Depends
from typing import Annotated
from sqlalchemy.orm import Session


def get_user_repo(db: Annotated[Session, Depends(get_db)]):
    return UserRepository(db)


def get_ban_repo(db: Annotated[Session, Depends(get_db)]):
    return BanRepository(db)

def get_chat_repo(db: Annotated[Session, Depends(get_db)]):
    return ChatRepository(db)

def get_favorite_track_repo(db: Annotated[Session, Depends(get_db)]):
    return FavoriteTrackRepository(db)

def get_friendship_repo(db: Annotated[Session, Depends(get_db)]):
    return FriendshipRepository(db)

def get_member_room_repo(db: Annotated[Session, Depends(get_db)]):
    return MemberRoomAssociationRepository(db)

def get_notification_repo(db: Annotated[Session, Depends(get_db)]):
    return NotificationRepository(db)

def get_room_repo(db: Annotated[Session, Depends(get_db)]):
    return RoomRepository(db)

def get_track_repo(db: Annotated[Session, Depends(get_db)]):
    return TrackRepository(db)

def get_room_track_repo(db: Annotated[Session, Depends(get_db)]):
    return RoomTrackAssociationRepository(db)