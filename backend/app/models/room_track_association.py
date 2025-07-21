from app.models.base import Base
from sqlalchemy import ForeignKey,DateTime,func,PrimaryKeyConstraint
from sqlalchemy.orm import Mapped,mapped_column,relationship
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID 
import uuid

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.room import Room
    from app.models.track import Track
    from app.models.user import User

class RoomTrackAssociationModel(Base):
    __tablename__ = 'room_track_association'

    __table_args__ = (
        PrimaryKeyConstraint('room_id', 'track_id'),
    )
    room_id: Mapped[int] = mapped_column(ForeignKey('rooms.id'),nullable=False)
    track_id: Mapped[int] = mapped_column(ForeignKey('tracks.id'),nullable=False)
    order_in_queue: Mapped[int] = mapped_column(nullable=True)
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),nullable=False,server_default=func.now())
    addded_by_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),nullable=False)

    user: Mapped['User'] = relationship(back_populates='room_track')
    room: Mapped['Room'] = relationship(back_populates='room_track')
    track: Mapped['Track'] = relationship(back_populates='room_track')