import uuid

from app.domain.interfaces.notification_gateway import NotificationGateway
from app.domain.interfaces.room_gateway import RoomGateway
from app.domain.interfaces.user_gateway import UserGateway
from app.domain.enum import NotificationType
from app.domain.entity import NotificationEntity

from app.domain.exceptions.exception import ServerError
from app.domain.exceptions.user_exception import UserNotFound
from app.domain.exceptions.room_exception import RoomNotFoundError

class CreateNotification:
    def __init__(self,notify_repo: NotificationGateway,user_repo: UserGateway,room_repo: RoomGateway):
        self.notify_repo = notify_repo
        self.user_repo = user_repo
        self.room_repo = room_repo
     
    def add_notification(
        self,
        user_id: uuid.UUID,
        notification_type: NotificationType,
        message: str,
        sender_id: uuid.UUID | None = None,
        room_id: uuid.UUID | None = None,
        related_object_id: uuid.UUID | None = None
    ) -> NotificationEntity:
        """
        Создает новую запись об уведомлении. Этот метод будет вызываться из других сервисов.

        Args:
            user_id (uuid.UUID): ID пользователя, который получит уведомление.
            notification_type (NotificationType): Тип уведомления (Enum).
            message (str): Текст уведомления.
            sender_id (Optional[uuid.UUID]): ID пользователя, который инициировал уведомление.
            room_id (Optional[uuid.UUID]): ID комнаты, если уведомление связано с комнатой.
            related_object_id (Optional[uuid.UUID]): ID объекта, к которому относится уведомление.
        """
        user = self.user_repo.get_user_by_id( user_id)
        if not user:
            raise UserNotFound()

        user = self.user_repo.get_user_by_id(sender_id)
        if not user:
            raise UserNotFound()

        room = self.room_repo.get_room_by_id( room_id)
        if not room:
            raise RoomNotFoundError()

        try:
            new_notification = self.notify_repo.add_notification(
                 user_id, notification_type, message, sender_id, room_id,related_object_id
            )
            return new_notification
        except Exception:
            raise ServerError(
                detail="Не удалось создать уведомление из-за внутренней ошибки сервера."
            )