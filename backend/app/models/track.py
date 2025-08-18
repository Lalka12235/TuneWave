from app.models.base import Base
from sqlalchemy.orm import Mapped,mapped_column,relationship
from sqlalchemy import UUID,JSON,DateTime,func
from typing import TYPE_CHECKING
import uuid
from datetime import datetime
from typing import Optional

if TYPE_CHECKING:
    from app.models.favorite_track import FavoriteTrack
    from app.models.room_track_association import RoomTrackAssociationModel

class Track(Base):
    __tablename__ = 'tracks'

    """
    Модель для хранения кешированных метаданных треков Spotify.
    Это позволяет избегать повторных запросов к Spotify API за одной и той же информацией.
    """
    __tablename__ = 'tracks'

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False
    )
    spotify_id: Mapped[str] = mapped_column(
        unique=True, nullable=False, index=True,
        comment="Уникальный ID трека в Spotify (например, '4o0c16W1T6nFz3E6w7P9Xl')"
    )
    spotify_uri: Mapped[str] = mapped_column(
        unique=True, nullable=False,
        comment="Spotify URI трека (например, 'spotify:track:4o0c16W1T6nFz3E6w7P9Xl')"
    )
    title: Mapped[str] = mapped_column(
        nullable=False,
        comment="Название трека."
    )
    artist_names: Mapped[list[str]] = mapped_column(
        JSON, nullable=False, 
        comment="Список имен артистов, связанных с треком (хранится как JSON-массив)."
    )
    album_name: Mapped[str] = mapped_column(
        nullable=False,
        comment="Название альбома, к которому относится трек."
    )
    album_cover_url: Mapped[str | None] = mapped_column( 
        nullable=True,
        comment="URL обложки альбома (предпочтительно высокого качества)."
    )
    duration_ms: Mapped[int] = mapped_column(
        nullable=False, 
        comment="Длительность трека в миллисекундах."
    )
    is_playable: Mapped[bool] = mapped_column( 
        nullable=False, default=True,
        comment="Указывает, доступен ли трек для воспроизведения (из Spotify API)."
    )
    spotify_track_url: Mapped[Optional[str]] = mapped_column( 
        nullable=True, 
        comment="URL трека на Spotify (из external_urls.spotify)."
    )
    last_synced_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False,
        comment="Время последней синхронизации метаданных трека с Spotify."
    )
    created_at: Mapped[datetime] = mapped_column( 
        DateTime(timezone=True), default=func.now(), nullable=False,
        comment="Время добавления записи трека в локальную базу данных."
    )


    favorite_track: Mapped[list['FavoriteTrack']] = relationship(back_populates='track')
    room_track: Mapped[list['RoomTrackAssociationModel']] = relationship(back_populates='track')