import uuid

from app.domain.interfaces.notification_gateway import NotificationGateway
from app.domain.entity import NotificationEntity

from app.domain.exceptions.exception import ServerError
from app.domain.exceptions.notification_exception import NotificationNotFound,NotificationNotPermission



class MarkReadNotification:
    def __init__(self,notify_repo: NotificationGateway):
        self.notify_repo = notify_repo
     
    def mark_notification_as_read(self, notification_id: uuid.UUID, current_user_id: uuid.UUID) -> NotificationEntity:
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
            return notification
        
        try:
            self.notify_repo.mark_notification_as_read(notification_id)
            return notification
        except Exception:
            raise ServerError(
                detail="Не удалось отметить уведомление как прочитанное из-за внутренней ошибки сервера."
            )