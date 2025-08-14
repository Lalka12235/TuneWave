from app.models.base import Base
from sqlalchemy import ForeignKey,DateTime,func,Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID 
import uuid
from typing import TYPE_CHECKING
from datetime import datetime
from app.schemas.enum import NotificationType

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.room import Room


class Notification(Base):
    __tablename__ = 'notifications'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),primary_key=True,unique=True,default=uuid.uuid4,nullable=False)
    user_id: Mapped[uuid.UUID]  = mapped_column(ForeignKey('users.id'),nullable=False)
    sender_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('users.id'),nullable=True,default=None)
    room_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('rooms.id'),nullable=True,default=None)
    notification_type: Mapped[NotificationType] = mapped_column(Enum(NotificationType),nullable=False)
    message: Mapped[str] = mapped_column(nullable=False)
    is_read: Mapped[bool] = mapped_column(nullable=False,default=False)
    related_object_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=True, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),default=func.now(),nullable=False)


    user: Mapped["User"] = relationship(
        foreign_keys=[user_id],
        back_populates="notifications_received"
    )
    
    sender: Mapped["User"]  = relationship( 
        foreign_keys=[sender_id],
        back_populates="notifications_sent"
    )
    
    room: Mapped["Room"]  = relationship( 
        foreign_keys=[room_id],
        back_populates="notifications"
    )