import uuid


from app.logger.log_config import logger
from app.repositories.abc.notification_repo import ABCNotificationRepository
from app.repositories.abc.room_repo import ABCRoomRepository
from app.repositories.abc.user_repo import ABCUserRepository
from app.schemas.enum import NotificationType
from app.schemas.notification_schemas import NotificationResponse

from app.services.mappers.notification_mapper import NotificationMapper

from app.exceptions.exception import ServerError
from app.exceptions.user_exception import UserNotFound
from app.exceptions.room_exception import RoomNotFoundError
from app.exceptions.notification_exception import NotificationNotFound,NotificationNotPermission


class NotificationService:

    def __init__(self,notify_repo: ABCNotificationRepository,user_repo: ABCUserRepository,room_repo: ABCRoomRepository,notify_mapper: NotificationMapper):
        self.notify_repo = notify_repo
        self.user_repo = user_repo
        self.room_repo = room_repo
        self.notify_mapper = notify_mapper


    def _check_user_exists(self, user_id: uuid.UUID):
        """Вспомогательный метод для проверки существования пользователя."""
        user = self.user_repo.get_user_by_id( user_id)
        if not user:
            raise UserNotFound()
        return user


    
    def _check_room_exists(self, room_id: uuid.UUID):
        """Вспомогательный метод для проверки существования комнаты."""
        room = self.room_repo.get_room_by_id( room_id)
        if not room:
            raise RoomNotFoundError()
        return room
        

    
    def get_user_notifications(self, user_id: uuid.UUID,limit: int = 10, offset: int = 0) -> list[NotificationResponse]:
        """
        Получает список уведомлений для указанного пользователя.
        """
        self._check_user_exists( user_id, "Пользователь для получения уведомлений не найден.")
        notifications = self.notify_repo.get_user_notification(user_id,limit,offset)
        if not notifications:
            return []
        

        return [self.notify_mapper.to_response(notification) for notification in notifications]
    

    
    def add_notification(
        self,
        user_id: uuid.UUID,
        notification_type: NotificationType,
        message: str,
        sender_id: uuid.UUID | None = None,
        room_id: uuid.UUID | None = None,
        related_object_id: uuid.UUID | None = None
    ) -> NotificationResponse:
        """
        Создает новую запись об уведомлении. Этот метод будет вызываться из других сервисов.

        Args:
            db (Session): Сессия базы данных.
            user_id (uuid.UUID): ID пользователя, который получит уведомление.
            notification_type (NotificationType): Тип уведомления (Enum).
            message (str): Текст уведомления.
            sender_id (Optional[uuid.UUID]): ID пользователя, который инициировал уведомление.
            room_id (Optional[uuid.UUID]): ID комнаты, если уведомление связано с комнатой.
            related_object_id (Optional[uuid.UUID]): ID объекта, к которому относится уведомление.

        Returns:
            NotificationResponse: Детали созданного уведомления.
        """
        self._check_user_exists( user_id, "Пользователь-получатель уведомления не найден.")

        if sender_id:
            self._check_user_exists( sender_id, "Отправитель уведомления не найден.")

        if room_id:
            self._check_room_exists( room_id, "Комната, связанная с уведомлением, не найдена.")

        
        try:
            new_notification = self.notify_repo.add_notification(
                 user_id, notification_type, message, sender_id, room_id,related_object_id
            )
            return self.notify_mapper.to_response(new_notification)
        except Exception:
            raise ServerError(
                detail="Не удалось создать уведомление из-за внутренней ошибки сервера."
            )
        
    
    
    def mark_notification_as_read(self, notification_id: uuid.UUID, current_user_id: uuid.UUID) -> NotificationResponse:
        """
        Отмечает конкретное уведомление как прочитанное.
        Только владелец уведомления может его отметить как прочитанное.
        """
        notification = self.notify_repo.get_notification_by_id(notification_id)
        if not notification:
            raise NotificationNotFound()
        
        if notification.user_id != current_user_id:
            raise NotificationNotPermission(
                detail="У вас нет прав для отметки этого уведомления как прочитанного."
            )
        
        if notification.is_read:
            return self.notify_mapper.to_response(notification)
        
        try:
            notification_update = self.notify_repo.mark_notification_as_read(notification_id)
            return self.notify_mapper.to_response(notification_update)
        except Exception:
            raise ServerError(
                detail="Не удалось отметить уведомление как прочитанное из-за внутренней ошибки сервера."
            )
        
    
    
    def delete_notification(self, notification_id: uuid.UUID, current_user_id: uuid.UUID) -> dict[str, str]:
        """
        Удаляет уведомление. Только владелец уведомления может его удалить.
        """
        notification = self.notify_repo.get_notification_by_id(notification_id)
        if not notification:
            raise NotificationNotFound()
        
        if notification.user_id != current_user_id:
            raise NotificationNotPermission(
                detail="У вас нет прав для удаление этого уведомления."
            )
        
        try:
            self.notify_repo.delete_notification(notification_id)
            return {
                "status": "success",
                "detail": "Уведомление успешно удалено."
            }
        except Exception:
            raise ServerError(
                detail="Не удалось удалить уведомление из-за внутренней ошибки сервера."
            )
