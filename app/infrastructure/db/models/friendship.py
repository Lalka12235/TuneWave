from app.infrastructure.db.models.base import Base
from sqlalchemy import ForeignKey,DateTime,func,Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID 
import uuid
from typing import TYPE_CHECKING
from datetime import datetime
from app.domain.enum import  FriendshipStatus

if TYPE_CHECKING:
    from app.infrastructure.db.models import User



class Friendship(Base):
    __tablename__ = 'friendships'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),primary_key=True,unique=True,nullable=False,default=uuid.uuid4)
    requester_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('users.id'),nullable=False)
    accepter_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('users.id'),nullable=False)
    status: Mapped[FriendshipStatus] = mapped_column(Enum(FriendshipStatus),default=FriendshipStatus.PENDING,nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),default=func.now(),nullable=False)
    accepted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),nullable=True)


    requester: Mapped["User"] = relationship(
        foreign_keys=[requester_id],
        back_populates="sent_friend_requests"
    )
    
    
    accepter: Mapped["User"] = relationship(
        foreign_keys=[accepter_id],
        back_populates="received_friend_requests"
    )