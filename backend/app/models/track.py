from app.models.base import Base
from sqlalchemy.orm import Mapped,mapped_column,relationship
from sqlalchemy import UUID
from typing import TYPE_CHECKING
import uuid

if TYPE_CHECKING:
    from app.models.favorite_track import FavoriteTrack
    from app.models.room_track_association import RoomTrackAssociationModel

class Track(Base):
    __tablename__ = 'tracks'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    spotify_track_id: Mapped[str] = mapped_column(unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(nullable=False)
    artist: Mapped[str] = mapped_column(nullable=False)
    album: Mapped[str] = mapped_column(nullable=True)
    duration_ms: Mapped[int] = mapped_column(nullable=True)
    image_url: Mapped[str] = mapped_column(nullable=True)
    spotify_track_url: Mapped[str] = mapped_column(nullable=True)
    spotify_uri: Mapped[str] = mapped_column(unique=True, nullable=False)

    favorite_track: Mapped[list['FavoriteTrack']] = relationship(back_populates='track')
    room_track: Mapped[list['RoomTrackAssociationModel']] = relationship(back_populates='track')