from app.models.base import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID 
import uuid
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.room import Room
    from app.models.favorite_track import FavoriteTrack
    from app.models.room_track_association import RoomTrackAssociationModel
    from app.models.member_room_association import Member_room_association
    from app.models.message import Message


class User(Base):
    __tablename__ = 'users'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    username: Mapped[str] = mapped_column(unique=True,index=True,nullable=False)
    email: Mapped[str] = mapped_column(unique=True,nullable=False)
    is_email_verified: Mapped[bool] = mapped_column(nullable=False)
    avatar_url: Mapped[str] = mapped_column(nullable=True,default=None)
    bio: Mapped[str] = mapped_column(nullable=True,default="")
    #google
    google_id: Mapped[str] = mapped_column(unique=True,nullable=True)
    google_image_url: Mapped[str] = mapped_column(nullable=True)
    google_access_token: Mapped[str] = mapped_column(nullable=True)
    google_refresh_token: Mapped[str] = mapped_column(nullable=True)
    google_token_expires_at: Mapped[int] = mapped_column(nullable=True)
    #spotify
    spotify_id: Mapped[str] = mapped_column(unique=True,nullable=True)
    spotify_profile_url: Mapped[str] = mapped_column(nullable=True)
    spotify_image_url: Mapped[str] = mapped_column(nullable=True)
    spotify_access_token: Mapped[str] = mapped_column(nullable=True)
    spotify_refresh_token: Mapped[str] = mapped_column(nullable=True)
    spotify_token_expires_at: Mapped[int] = mapped_column(nullable=True)

    room: Mapped[list['Room']] = relationship(back_populates='user')
    favorite_track: Mapped[list['FavoriteTrack']] = relationship(back_populates='user')
    room_track: Mapped[list['RoomTrackAssociationModel']] = relationship(back_populates='user')
    member_room: Mapped[list['Member_room_association']] = relationship(back_populates='user')
    message: Mapped[list['Message']] = relationship(back_populates='user')