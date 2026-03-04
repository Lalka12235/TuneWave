import uuid

from app.domain.interfaces.notification_gateway import NotificationGateway
from app.domain.interfaces.user_gateway import UserGateway
from app.domain.entity import NotificationEntity
from app.domain.exceptions.user_exception import UserNotFound

class ReadNotification:
    def __init__(self,notify_repo: NotificationGateway,user_repo: UserGateway):
        self.notify_repo = notify_repo
        self.user_repo = user_repo
     
    def get_user_notifications(self, user_id: uuid.UUID,limit: int = 10, offset: int = 0) -> list[NotificationEntity]:
        """
        Получает список уведомлений для указанного пользователя.
        """
        user = self.user_repo.get_user_by_id( user_id)
        if not user:
            raise UserNotFound()
        notifications = self.notify_repo.get_user_notification(user_id,limit,offset)
        if not notifications:
            return []
        

        return [notification for notification in notifications]