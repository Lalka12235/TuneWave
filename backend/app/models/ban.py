from app.models.base import Base
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship, Mapped,mapped_column
from app.models.user import UserModel
from app.models.room import RoomModel
from datetime import datetime

class BanModel(Base):
    __tablename__ = 'bans'

    id: Mapped[int] = mapped_column(primary_key=True)
    reason: Mapped[str]
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    room_id: Mapped[int] = mapped_column(ForeignKey('room.id'))
    ban_expired: Mapped[datetime]

    user: Mapped[list['UserModel']] = relationship(back_populates='bans')
    room: Mapped['RoomModel'] = relationship(back_populates='bans')