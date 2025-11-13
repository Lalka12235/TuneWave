from dataclasses import dataclass
import uuid
from datetime import datetime


@dataclass(slots=True,frozen=True)
class MessageEntity:
    """
    Сущность модели Message
    """
    id: uuid.UUID
    text: str
    user_id: uuid.UUID
    room_id: uuid.UUID
    created_at: datetime