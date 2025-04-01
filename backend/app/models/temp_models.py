from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped,mapped_column,relationship



class Base(DeclarativeBase):
    pass


class RoomModel(Base):
    __tablename__ = 'rooms'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    owner_id: Mapped[int] = mapped_column(ForeignKey('users.id'), unique=True)

    # Связь "один-к-одному" с UserModel (комната принадлежит только одному пользователю)
    owner: Mapped['UserModel'] = relationship(back_populates='room')

    # Связь "один-ко-многим" с RoomTracksModel (в комнате могут быть несколько треков)
    room_tracks: Mapped[list['RoomTracksModel']] = relationship(back_populates='room')

    # Связь "один-ко-многим" с RoomMembersModel (в комнате может быть несколько участников)
    room_members: Mapped[list['RoomMembersModel']] = relationship(back_populates='room')


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

    # Связь "многие-к-одному" с RoomModel (одна комната содержит несколько участников)
    room: Mapped['RoomModel'] = relationship(back_populates='room_members')

    # Связь "многие-к-одному" с UserModel (один пользователь может состоять только в одной комнате)
    user: Mapped['UserModel'] = relationship()


class UserModel(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str]
    email: Mapped[str]
    password_hash: Mapped[str]

    # Связь "один-к-одному" с RoomModel (у пользователя может быть только одна комната)
    room: Mapped['RoomModel'] = relationship(back_populates='owner', uselist=False)

    # Связь "один-ко-многим" с TrackModel (пользователь может добавлять несколько треков)
    tracks: Mapped[list['TrackModel']] = relationship(back_populates='user')


class TrackModel(Base):
    __tablename__ = 'tracks'

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    artist: Mapped[str]
    genre: Mapped[str]
    url: Mapped[str]
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))

    # Связь "многие-к-одному" с UserModel (один пользователь может добавлять много треков)
    user: Mapped['UserModel'] = relationship(back_populates='tracks')

    # Связь "один-ко-многим" с RoomTracksModel (один трек может быть в нескольких комнатах)
    room_tracks: Mapped[list['RoomTracksModel']] = relationship(back_populates='track')
