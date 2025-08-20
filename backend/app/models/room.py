from app.models.base import Base
from sqlalchemy import ForeignKey,func,DateTime
from sqlalchemy.orm import Mapped,mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID 
import uuid
from typing import TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.track import Track
    from app.models.room_track_association import RoomTrackAssociationModel
    from app.models.member_room_association import Member_room_association
    from app.models.message import Message
    from app.models.ban import Ban
    from app.models.notification import Notification

class Room(Base):
    __tablename__ = 'rooms'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(index=True,nullable=False)
    max_members: Mapped[int] = mapped_column(nullable=False)
    owner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),ForeignKey('users.id'),nullable=False)
    is_private: Mapped[bool] = mapped_column(default=False,nullable=True)
    password_hash: Mapped[str] = mapped_column(nullable=True)
    current_track_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True),ForeignKey('tracks.id'),nullable=True)
    current_track_position_ms: Mapped[int | None] = mapped_column(nullable=True)
    is_playing: Mapped[bool] = mapped_column(default=False,nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    playback_host_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey('users.id', ondelete="SET NULL"), nullable=True, comment="ID пользователя, который является хостом воспроизведения для этой комнаты."
    )
    active_spotify_device_id: Mapped[str | None] = mapped_column(
        nullable=True, comment="ID активного устройства Spotify хоста воспроизведения."
    )
    current_playing_track_association_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey('room_track_associations.id', ondelete="SET NULL"), nullable=True, comment="ID записи в очереди (RoomTrackAssociationModel) для текущего играющего трека."
    )
    current_playback_progress_ms: Mapped[int | None] = mapped_column(
        nullable=True, comment="Текущий прогресс воспроизведения трека в миллисекундах."
    )
    is_playing: Mapped[bool] = mapped_column(
        default=False, nullable=False, comment="Флаг, указывающий, находится ли плеер в режиме воспроизведения (True) или паузы (False)."
    )


    user: Mapped['User'] = relationship(back_populates='room')
    current_track: Mapped["Track | None"] = relationship("Track", lazy="joined")
    room_track: Mapped[list['RoomTrackAssociationModel']] = relationship(back_populates='room')
    member_room: Mapped[list['Member_room_association']] = relationship(back_populates='room')
    message: Mapped[list['Message']] = relationship(back_populates='room')
    banned: Mapped['Ban'] = relationship(back_populates='room')
    playback_host: Mapped["User | None"] = relationship(foreign_keys=[playback_host_id])

    # Новая связь для текущего играющего трека в очереди
    current_playing_track_assoc: Mapped["RoomTrackAssociationModel | None"] = relationship(foreign_keys=[current_playing_track_association_id])


    notifications: Mapped[list["Notification"]] = relationship(
        back_populates="room"
    )   