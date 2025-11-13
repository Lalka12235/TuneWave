from dataclasses import dataclass
import uuid
from datetime import datetime
from app.domain.enum.enum import NotificationType


@dataclass(slots=True,frozen=True)
class NotificationEntity:
    """
    Сущность модели Notification
    """
    id: uuid.UUID
    user_id: uuid.UUID
    sender_id: uuid.UUID
    room_id: uuid.UUID
    notification_type: NotificationType
    message: str
    is_read: bool
    related_object_id: uuid.UUID
    created_at: datetime