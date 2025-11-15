from app.infrastructure.db.models.base import Base
from sqlalchemy import ForeignKey, DateTime,func, PrimaryKeyConstraint
from sqlalchemy.orm import Mapped,mapped_column, relationship

from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID 
import uuid

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.infrastructure.db.models.user import User
    from app.infrastructure.db.models.track import Track

class FavoriteTrack(Base):
    __tablename__ = 'favorite_tracks'

    __table_args__ = (
        PrimaryKeyConstraint('user_id', 'track_id'),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),ForeignKey('users.id'),nullable=False)
    track_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),ForeignKey('tracks.id'),nullable=False)
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),nullable=False, server_default=func.now())

    user: Mapped['User'] = relationship(back_populates='favorite_track')
    track: Mapped['Track'] = relationship(back_populates='favorite_track')