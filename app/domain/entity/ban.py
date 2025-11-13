from dataclasses import dataclass
import uuid
from datetime import datetime


@dataclass(slots=True,frozen=True)
class BanEntity:
    """
    Сущность модели Ban
    """
    id: uuid.UUID
    ban_user_id: uuid.UUID
    room_id: uuid.UUID
    reason: str
    ban_date: datetime
    by_ban_user_id: uuid.UUID