from app.models.base import Base
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.room import RoomModel
from app.models.track import TrackModel
from app.models.ban import BanModel

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

    ban: Mapped['BanModel'] = relationship(back_populates='user')
