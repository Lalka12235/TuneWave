from app.models.base import Base
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped,mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID 
import uuid
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.track import Track
    from app.models.room_track_association import RoomTrackAssociationModel
    from app.models.member_room_association import Member_room_association

class Room(Base):
    __tablename__ = 'rooms'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(nullable=False)
    max_members: Mapped[int] = mapped_column(nullable=False)
    owner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),ForeignKey('users.id'),nullable=False)
    is_private: Mapped[bool] = mapped_column(nullable=True)
    password_hash: Mapped[str] = mapped_column(nullable=True)
    current_track_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),ForeignKey('tracks.id'),nullable=True)
    current_track_position_ms: Mapped[int] = mapped_column(nullable=True)
    is_playing: Mapped[bool] = mapped_column(nullable=False)

    user: Mapped['User'] = relationship(back_populates='room')
    current_track: Mapped["Track | None"] = relationship("Track", lazy="joined")
    room_track: Mapped[list['RoomTrackAssociationModel']] = relationship(back_populates='room')
    member_room: Mapped[list['Member_room_association']] = relationship(back_populates='room')