from app.models.base import Base
from sqlalchemy import ForeignKey, DateTime,func,PrimaryKeyConstraint
from sqlalchemy.orm import Mapped,mapped_column,relationship
from datetime import datetime

from sqlalchemy.dialects.postgresql import UUID 
import uuid

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.room import Room

class Member_room_association(Base):
    __tablename__ = 'member_room_association'

    __table_args__ = (
        PrimaryKeyConstraint('user_id', 'room_id'),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),ForeignKey('users.id'),nullable=False)
    room_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),ForeignKey('rooms.id'),nullable=False)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),nullable=False,server_default=func.now())

    user: Mapped['User'] = relationship(back_populates='member_room')
    room: Mapped['Room'] = relationship(back_populates='member_room')