from fastapi import HTTPException,status
from app.schemas.notification_schemas import NotificationResponse
import uuid
from sqlalchemy.orm import Session
from app.repositories.notification_repo import NotificationRepository
from app.models import Notification
from app.repositories.user_repo import UserRepository
from app.repositories.room_repo import RoomRepository
from app.schemas.enum import NotificationType
from app.logger.log_config import logger


class NotificationService:

    @staticmethod
    def _map_notification_to_response(notification: Notification) -> NotificationResponse:
        """
        Вспомогательный метод для маппинга объекта Notification SQLAlchemy в Pydantic NotificationResponse.
        """
        return NotificationResponse.model_validate(notification)
    

    @staticmethod
    def _check_user_exists(db: Session, user_id: uuid.UUID, detail_message: str):
        """Вспомогательный метод для проверки существования пользователя."""
        user = UserRepository.get_user_by_id(db, user_id)
        logger.debug('NotificationService: Выполняем поиск пользователя по ID %s в базе данных',str(user_id))
        if not user:
            logger.error('NotificationService: Во время поиска по ID пользователь %s не был найден в базе данных',str(user_id))
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail_message)
        return user


    @staticmethod
    def _check_room_exists(db: Session, room_id: uuid.UUID, detail_message: str):
        """Вспомогательный метод для проверки существования комнаты."""
        room = RoomRepository.get_room_by_id(db, room_id)
        logger.debug('NotificationService: Выполняем поиск комнаты по ID %s в базе данных',str(room_id))
        if not room:
            logger.error('NotificationService: Во время поиска комнаты по ID %s не был найден в базе данных',str(room_id))
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail_message)
        return room
        

    @staticmethod
    def get_user_notifications(db: Session, user_id: uuid.UUID,limit: int = 10, offset: int = 0) -> list[NotificationResponse]:
        """
        Получает список уведомлений для указанного пользователя.
        """
        NotificationService._check_user_exists(db, user_id, "Пользователь для получения уведомлений не найден.")
        notifications = NotificationRepository.get_user_notification(db,user_id,limit,offset)
        if not notifications:
            logger.warning('NotificationService: Список уведомлений у пользователя %s пуст',str(user_id))
            return []
        

        return [NotificationService._map_notification_to_response(notification) for notification in notifications]
    

    @staticmethod
    def add_notification(
        db: Session,
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
        NotificationService._check_user_exists(db, user_id, "Пользователь-получатель уведомления не найден.")

        if sender_id:
            NotificationService._check_user_exists(db, sender_id, "Отправитель уведомления не найден.")

        if room_id:
            NotificationService._check_room_exists(db, room_id, "Комната, связанная с уведомлением, не найдена.")

        
        try:
            new_notification = NotificationRepository.add_notification(
                db, user_id, notification_type, message, sender_id, room_id,related_object_id
            )
            logger.info('NotificationService: Уведомление было успешно от %s к %s для входа в комнату %s',str(sender_id),str(user_id),str(room_id))
            db.commit()
            db.refresh(new_notification)
            return NotificationService._map_notification_to_response(new_notification)
        except HTTPException as e:
            logger.error('NotificationService: Произошла ошибка при попытке отправить уведомление от %s к %s для комнаты %s.%r',str(sender_id),str(user_id),str(room_id),e.detail,exc_info=True)
            db.rollback()
            raise e
        except Exception:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Не удалось создать уведомление из-за внутренней ошибки сервера."
            )
        
    
    @staticmethod
    def mark_notification_as_read(db: Session, notification_id: uuid.UUID, current_user_id: uuid.UUID) -> NotificationResponse:
        """
        Отмечает конкретное уведомление как прочитанное.
        Только владелец уведомления может его отметить как прочитанное.
        """
        notification = NotificationRepository.get_notification_by_id(db,notification_id)
        if not notification:
            logger.warning('NotificationService: Уведомление по ID %s не было найдено',str(notification_id))
            raise HTTPException(
                status_code=404,
                detail='Уведомление не найдено'
            )
        
        if notification.user_id != current_user_id:
            logger.warning('NotificationService: Произошла ошибка при отметки уведомления')
            raise HTTPException(
                status_code=403,
                detail="У вас нет прав для отметки этого уведомления как прочитанного."
            )
        
        if notification.is_read:
            return NotificationService._map_notification_to_response(notification)
        
        try:
            notification_update = NotificationRepository.mark_notification_as_read(db,notification_id)
            logger.info('NotificationService: Сообщение успешном отмечено прочитаным по ID %s',str(notification_id))
            db.commit()
            db.refresh(notification_update)
            return NotificationService._map_notification_to_response(notification_update)
        except HTTPException as e:
            logger.error(f'NotificationService: произошла ошибка при попытке прочтения уведомления {notification_id} от пользователя {notification.sender_id} к пользователю {notification.user_id}.{e}',exc_info=True)
            db.rollback()
            raise e
        except Exception:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Не удалось отметить уведомление как прочитанное из-за внутренней ошибки сервера."
            )
        
    
    @staticmethod
    def delete_notification(db: Session, notification_id: uuid.UUID, current_user_id: uuid.UUID) -> dict[str, str]:
        """
        Удаляет уведомление. Только владелец уведомления может его удалить.
        """
        notification = NotificationRepository.get_notification_by_id(db,notification_id)
        logger.warning('NotificationService: Уведомление по ID %s не было найдено',str(notification_id))
        if not notification:
            raise HTTPException(
                status_code=404,
                detail='Уведомление не найдено'
            )
        
        if notification.user_id != current_user_id:
            logger.warning('NotificationService: Произошла ошибка при удалении уведомления')
            raise HTTPException(
                status_code=403,
                detail="У вас нет прав для удаление этого уведомления."
            )
        
        try:
            NotificationRepository.delete_notification(db,notification_id)
            logger.info('NotificationService: Сообщение успешном удалено по ID %s',str(notification_id))
            db.commit()
            return {
                "status": "success",
                "detail": "Уведомление успешно удалено."
            }
        except HTTPException as e:
            logger.error('NotificationService: произошла ошибка при попытке удаления уведомления %s.%r',str(notification_id),e.detail,exc_info=True)
            db.rollback()
            raise e
        except Exception:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Не удалось удалить уведомление из-за внутренней ошибки сервера."
            )
