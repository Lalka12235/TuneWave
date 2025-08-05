from app.models.base import Base
from sqlalchemy import ForeignKey, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID 
import uuid
from typing import TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from app.models.room import Room
    from app.models.user import User



class Message(Base):
    __tablename__ = 'messages'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4,nullable=False,unique=True)
    text: Mapped[str] = mapped_column(Text,nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),ForeignKey('users.id'),nullable=False)
    room_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),ForeignKey('rooms.id'),nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime,default=datetime.utcnow,nullable=False)

    user: Mapped['User'] = relationship(back_populates='message')
    room: Mapped['Room'] = relationship(back_populates='message')
