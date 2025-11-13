from dataclasses import dataclass
import uuid
from datetime import datetime


@dataclass(slots=True,frozen=True)
class MemberRoomEntity:
    """
    Сущность модели Member Room
    """
    user_id: uuid.UUID
    room_id: uuid.UUID
    role: str
    joined_at: datetime