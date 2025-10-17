from sqlalchemy import select,delete,update
from sqlalchemy.orm import Session,joinedload
from app.models.notification import Notification
import uuid
from app.schemas.enum import NotificationType


class NotificationRepository:
    """
    Репозиторий для выполнения операций CRUD над моделью Notification.
    Отвечает за управление записями уведомлений.
    """

    def __init__(self, db: Session):
        self.self = db


    
    def get_notification_by_id(self,notification_id: uuid.UUID) -> Notification | None:
        """
        Получает запись об уведомлении по её ID.
        Загружает отношения user, sender и room для удобства.

        Args:
            db (Session): Сессия базы данных SQLAlchemy.
            notification_id (uuid.UUID): ID записи об уведомлении.

        Returns:
            Optional[Notification]: Объект Notification или None, если не найден.
        """
        stmt = select(Notification).options(
                joinedload(Notification.user),
                joinedload(Notification.sender),
                joinedload(Notification.room)
        ).where(Notification.id == notification_id)
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()
    

    
    def get_user_notification(self,user_id: uuid.UUID,limit: int = 10, offset: int = 0) -> list[Notification]:
        """
        Получает список уведомлений для указанного пользователя.
        Может быть отфильтрован по статусу прочитанности.

        Args:
            db (Session): Сессия базы данных SQLAlchemy.
            user_id (uuid.UUID): ID пользователя, для которого ищутся уведомления.
            is_read (Optional[bool]): Фильтр по статусу прочитанности (True, False или None для всех).
            limit (int): Максимальное количество уведомлений для возврата.
            offset (int): Смещение для пагинации.

        Returns:
            List[Notification]: Список объектов Notification.
        """
        stmt = select(Notification).options(
                joinedload(Notification.user),
                joinedload(Notification.sender),
                joinedload(Notification.room)
            ).where(Notification.user_id == user_id
            ).order_by(Notification.created_at.desc()
            ).limit(limit
            ).offset(offset)
        result = self.db.execute(stmt)
        return result.scalars().all()
    

    
    def add_notification(
        self,
        user_id: uuid.UUID,
        notification_type: NotificationType,
        message: str,
        sender_id: uuid.UUID | None = None,
        room_id: uuid.UUID | None = None,
        related_object_id: uuid.UUID | None = None,
    ) -> Notification:
        """
        Создает новую запись об уведомлении.

        Args:
            db (Session): Сессия базы данных SQLAlchemy.
            user_id (uuid.UUID): ID пользователя-получателя уведомления.
            notification_type (NotificationType): Тип уведомления.
            message (str): Текст уведомления.
            sender_id (Optional[uuid.UUID]): ID отправителя уведомления (если применимо).
            room_id (Optional[uuid.UUID]): ID комнаты, к которой относится уведомление (если применимо).
            related_object_id (Optional[uuid.UUID]): ID связанного объекта (например, friendship_id).

        Returns:
            Notification: Созданный объект Notification.
        """
        new_notification = Notification(
            user_id=user_id,
            sender_id=sender_id,
            room_id=room_id,
            notification_type=notification_type,
            message=message,
            related_object_id=related_object_id,
        )
        self.db.add(new_notification)
        self.db.flush()
        return new_notification
    

    
    def mark_notification_as_read(self,notification_id: uuid.UUID) -> Notification:
        """
        Отмечает конкретное уведомление как прочитанное.

        Args:
            db (Session): Сессия базы данных SQLAlchemy.
            notification_id (uuid.UUID): ID уведомления для отметки.

        Returns:
            Optional[Notification]: Обновленный объект Notification или None, если не найден.
        """
        stmt = update(Notification).where(
            Notification.id == notification_id
        ).values(is_read=True)
        result = self.db.execute(stmt)
        return result
    

    
    def delete_notification(self,notification_id: uuid.UUID) -> bool:
        """
        Удаляет запись об уведомлении по её ID.

        Args:
            db (Session): Сессия базы данных SQLAlchemy.
            notification_id (uuid.UUID): ID уведомления для удаления.

        Returns:
            bool: True, если запись была успешно удалена, иначе False.
        """
        stmt = delete(Notification).where(
            Notification.id == notification_id,
        )
        result = self.db.execute(stmt)
        return result.rowcount > 0