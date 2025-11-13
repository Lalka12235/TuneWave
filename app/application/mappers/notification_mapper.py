from app.infrastracture.db.models import Notification
from app.presentation.schemas.notification_schemas import NotificationResponse
from app.application.mappers.base_mapper import BaseMapper
from app.application.mappers.user_mapper import UserMapper

class NotificationMapper(BaseMapper):
    def __init__(self, user_mapper: UserMapper):
        self._user_mapper = user_mapper

    def to_response(self, notification: Notification) -> NotificationResponse:
        return NotificationResponse(
            id=notification.id,
            recipient=self._user_mapper.to_response(notification.recipient),
            type=notification.type,
            content=notification.content,
            created_at=notification.created_at,
            is_read=notification.is_read
        )