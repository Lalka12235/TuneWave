import uuid

from app.domain.interfaces.notification_gateway import NotificationGateway

class DeleteNotification:
    def __init__(self,notify_repo: NotificationGateway):
        self.notify_repo = notify_repo
     
    def delete_notification(self, notification_id: uuid.UUID) -> dict[str, str]:
        """
        Удаляет уведомление. Только владелец уведомления может его удалить.
        """
        deleted_successful = self.notify_repo.delete_notification(notification_id)
        if deleted_successful:
            return {
                    "status": str(deleted_successful),
                    "detail": "Уведомление успешно удалено."
            }
        else:
            return {
                    "status": str(deleted_successful),
                    "detail": "Уведомление не удалено."
            }