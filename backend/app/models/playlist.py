from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base
from app.models.user import UserModel
from app.models.track import TrackModel


class PlaylistModel(Base):
    __tablename__ = 'playlists'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))

    # Связь "многие-к-одному" с UserModel (плейлист принадлежит одному пользователю)
    user: Mapped['UserModel'] = relationship(back_populates='playlists')

    # Связь "один-ко-многим" с PlaylistTracksModel (плейлист содержит несколько треков)
    playlist_tracks: Mapped[list['PlaylistTracksModel']] = relationship(back_populates='playlist', cascade="all, delete-orphan")


class PlaylistTracksModel(Base):
    __tablename__ = 'playlist_tracks'

    id: Mapped[int] = mapped_column(primary_key=True)
    playlist_id: Mapped[int] = mapped_column(ForeignKey('playlists.id'))
    track_id: Mapped[int] = mapped_column(ForeignKey('tracks.id'))

    # Связь "многие-к-одному" с PlaylistModel (плейлист содержит треки)
    playlist: Mapped['PlaylistModel'] = relationship(back_populates='playlist_tracks')

    # Связь "многие-к-одному" с TrackModel (трек может быть в нескольких плейлистах)
    track: Mapped['TrackModel'] = relationship(back_populates='playlist_tracks')