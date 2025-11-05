from app.models.base import Base
from sqlalchemy import ForeignKey, DateTime,UUID,func
from sqlalchemy.orm import Mapped,mapped_column, relationship
from typing import TYPE_CHECKING
from datetime import datetime
import uuid

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.room import Room


class Ban(Base):
    """
    Модель базы данных
    """
    __tablename__ = 'bans'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False, default=uuid.uuid4, unique=True)
    ban_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('users.id'), nullable=False)
    room_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('rooms.id'), nullable=True)
    reason: Mapped[str] = mapped_column(nullable=True)
    ban_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), nullable=False)
    by_ban_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('users.id'), nullable=False)

    banned_user: Mapped["User"] = relationship(
        foreign_keys=[ban_user_id],
        back_populates="bans_received"
    )
    
    banned_by_user: Mapped["User"] = relationship(
        foreign_keys=[by_ban_user_id],
        back_populates="bans_issued" 
    )
    room: Mapped['Room'] = relationship(back_populates='banned')