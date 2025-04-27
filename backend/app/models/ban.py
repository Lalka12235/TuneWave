from app.models.base import Base
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship, Mapped,mapped_column
from datetime import datetime

class BanModel(Base):
    __tablename__ = 'bans'

    id: Mapped[int] = mapped_column(primary_key=True)
    reason: Mapped[str]
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    room_id: Mapped[int] = mapped_column(ForeignKey('rooms.id')) 
    ban_expired: Mapped[datetime]

    user: Mapped['UserModel'] = relationship(back_populates='ban') 
    room: Mapped['RoomModel'] = relationship(back_populates='bans')