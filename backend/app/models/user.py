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

    room: Mapped['RoomModel'] = relationship(back_populates='owner', uselist=False)
    tracks: Mapped[list['TrackModel']] = relationship(back_populates='user')
    ban: Mapped[list['BanModel']] = relationship(back_populates='user')