from app.models.base import Base
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped,mapped_column,relationship
from app.models.user import UserModel
from app.models.track import TrackModel
from app.models.ban import BanModel

class RoomModel(Base):
    __tablename__ = 'rooms'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    max_member: Mapped[int]
    is_private: Mapped[bool]
    password: Mapped[str]
    owner_id: Mapped[int] = mapped_column(ForeignKey('users.id'), unique=True)

    owner: Mapped['UserModel'] = relationship(back_populates='room')
    room_tracks: Mapped[list['RoomTracksModel']] = relationship(back_populates='room')
    room_members: Mapped[list['RoomMembersModel']] = relationship(back_populates='room')
    bans: Mapped[list['BanModel']] = relationship(back_populates='room') 


class RoomTracksModel(Base):
    __tablename__ = 'room_tracks'

    id: Mapped[int] = mapped_column(primary_key=True)
    room_id: Mapped[int] = mapped_column(ForeignKey('rooms.id'))
    track_id: Mapped[int] = mapped_column(ForeignKey('tracks.id'))

    # Связь "многие-к-одному" с RoomModel (одна комната содержит много треков)
    room: Mapped['RoomModel'] = relationship(back_populates='room_tracks')

    # Связь "многие-к-одному" с TrackModel (один трек может быть в разных комнатах)
    track: Mapped['TrackModel'] = relationship(back_populates='room_tracks')


class RoomMembersModel(Base):
    __tablename__ = 'room_members'

    id: Mapped[int] = mapped_column(primary_key=True)
    room_id: Mapped[int] = mapped_column(ForeignKey('rooms.id'))
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    role: Mapped[str]

    # Связь "многие-к-одному" с RoomModel (одна комната содержит несколько участников)
    room: Mapped['RoomModel'] = relationship(back_populates='room_members')

    # Связь "многие-к-одному" с UserModel (один пользователь может состоять только в одной комнате)
    user: Mapped['UserModel'] = relationship()
