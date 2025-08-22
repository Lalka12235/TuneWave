from app.models.base import Base
from sqlalchemy import ForeignKey,DateTime,func
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
    """
    Модель, представляющая трек в очереди воспроизведения конкретной комнаты.
    Каждая запись - это один трек в очереди с его порядком и статусом.
    """
    __tablename__ = 'room_track_associations'

    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    room_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('rooms.id',ondelete="CASCADE"), nullable=False)
    track_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('tracks.id',ondelete="CASCADE"), nullable=False)
    order_in_queue: Mapped[int] = mapped_column(nullable=False)
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    added_by_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)

    room: Mapped["Room"] = relationship(
        back_populates="room_track",
        primaryjoin="RoomTrackAssociationModel.room_id == Room.id"
    )
    user: Mapped["User"] = relationship(
        back_populates="room_track",
        primaryjoin="RoomTrackAssociationModel.added_by_user_id == User.id"
    )
    track: Mapped['Track'] = relationship(back_populates='room_track')