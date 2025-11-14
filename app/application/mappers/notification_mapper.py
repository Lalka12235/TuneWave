from app.domain.entity import NotificationEntity
from app.presentation.schemas.notification_schemas import NotificationResponse
from app.application.mappers.user_mapper import UserMapper

class NotificationMapper:
    def __init__(self, user_mapper: UserMapper):
        self._user_mapper = user_mapper

    def to_response(self, notification: NotificationEntity) -> NotificationResponse:
        return NotificationResponse(

        )