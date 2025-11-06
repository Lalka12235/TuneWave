from dataclasses import dataclass
import uuid
from datetime import datetime


@dataclass
class MemberRoomEntity:
    user_id: uuid.UUID
    room_id: uuid.UUID
    role: str
    joined_at: datetime