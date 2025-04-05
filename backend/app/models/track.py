from app.models.base import Base
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped,mapped_column,relationship
from app.models.user import UserModel
from app.models.room import RoomTracksModel

class TrackModel(Base):
    __tablename__ = 'tracks'

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    artist: Mapped[str]
    genre: Mapped[str]
    url: Mapped[str]
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))


    user: Mapped['UserModel'] = relationship(back_populates='tracks')

    room_tracks: Mapped[list['RoomTracksModel']] = relationship(back_populates='track')
