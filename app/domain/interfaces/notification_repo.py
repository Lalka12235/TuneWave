from abc import abstractmethod,ABC
import uuid
from app.domain.entity.notification import NotificationEntity
from app.domain.enum import NotificationType


class NotificationRepository(ABC):
    """
    Абстрактный репозиторий для работы с уведомлениями.
    """

    @abstractmethod
    def get_notification_by_id(self,notification_id: uuid.UUID) -> NotificationEntity | None:
        """
        Получает запись об уведомлении по её ID.
        Загружает отношения user, sender и room для удобства.
        """
        raise NotImplementedError()

    @abstractmethod
    def get_user_notification(self,user_id: uuid.UUID,limit: int = 10, offset: int = 0) -> list[NotificationEntity]:
        """
        Получает список уведомлений для указанного пользователя.
        Может быть отфильтрован по статусу прочитанности.
        """
        raise NotImplementedError()
    
    @abstractmethod
    def add_notification(
        self,
        user_id: uuid.UUID,
        notification_type: NotificationType,
        message: str,
        sender_id: uuid.UUID | None = None,
        room_id: uuid.UUID | None = None,
        related_object_id: uuid.UUID | None = None,
    ) -> NotificationEntity:
        """
        Создает новую запись об уведомлении.
        """
        raise NotImplementedError()

    @abstractmethod
    def mark_notification_as_read(self,notification_id: uuid.UUID) -> bool:
        """
        Отмечает конкретное уведомление как прочитанное.
        """
        raise NotImplementedError()

    @abstractmethod
    def delete_notification(self,notification_id: uuid.UUID) -> bool:
        """
        Удаляет запись об уведомлении по её ID.
        """
        raise NotImplementedError()