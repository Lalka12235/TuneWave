from app.models.base import Base
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped,mapped_column,relationship
from datetime import  datetime

class RoomModel(Base):
    __tablename__ = 'rooms'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    max_member: Mapped[int]
    is_private: Mapped[bool]
    password: Mapped[str]
    owner_id: Mapped[int] = mapped_column(ForeignKey('users.id'), unique=True)
    current_track_id: Mapped[int] = mapped_column(ForeignKey('tracks.id'))
    player_state: Mapped[str] = mapped_column(default='paused')


    owner: Mapped['UserModel'] = relationship(back_populates='room')
    room_tracks: Mapped[list['RoomTracksModel']] = relationship(back_populates='room')
    room_members: Mapped[list['RoomMembersModel']] = relationship(back_populates='room')
    bans: Mapped[list['BanModel']] = relationship(back_populates='room') 


class RoomTracksModel(Base):
    __tablename__ = 'room_tracks'

    id: Mapped[int] = mapped_column(primary_key=True)
    room_id: Mapped[int] = mapped_column(ForeignKey('rooms.id'))
    track_id: Mapped[int] = mapped_column(ForeignKey('tracks.id'))
    position: Mapped[int]

    room: Mapped['RoomModel'] = relationship(back_populates='room_tracks')

    track: Mapped['TrackModel'] = relationship(back_populates='room_tracks')


class RoomMembersModel(Base):
    __tablename__ = 'room_members'

    id: Mapped[int] = mapped_column(primary_key=True)
    room_id: Mapped[int] = mapped_column(ForeignKey('rooms.id'))
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    role: Mapped[str]

    room: Mapped['RoomModel'] = relationship(back_populates='room_members')

    user: Mapped['UserModel'] = relationship()
