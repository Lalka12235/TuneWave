import uuid
from app.config.log_config import logger
from app.domain.enum import NotificationType
from app.domain.exceptions.user_exception import UserNotFound
from app.domain.interfaces.friendship_gateway import FriendshipGateway
from app.domain.interfaces.user_gateway import UserGateway
from app.domain.interfaces.notification_gateway import NotificationGateway
from app.infrastructure.ws.manager_notify_service import NotifyService

from app.domain.exceptions.exception import ServerError
from app.domain.exceptions.friendship_exception import (
    FriendshipNotFoundError,
    FriendshipPermissionError,
)


class DeleteFreidnship:
    def __init__(
        self,
        friend_repo: FriendshipGateway,
        notify_repo: NotificationGateway,
        user_repo: UserGateway,
        notify_service: NotifyService
    ):
        self.friend_repo = friend_repo
        self.notify_repo = notify_repo
        self.user_repo = user_repo
        self.notify_service = notify_service

    async def delete_friendship(
        self, friendship_id: uuid.UUID, current_user_id: uuid.UUID
    ) -> dict[str, str]:
        """
        Отклоняет ожидающий запрос на дружбу.
        """
        friendship = self.friend_repo.get_friendship_by_id(friendship_id)
        if not friendship:
            raise FriendshipNotFoundError()

        if current_user_id not in [friendship.requester_id, friendship.accepter_id]:
            raise FriendshipPermissionError(
                detail="У вас нет прав для удаления этой записи о дружбе.",
            )
        accepter = self.user_repo.get_user_by_id(friendship.accepter_id)
        if not accepter:
            raise UserNotFound()
        requester = self.user_repo.get_user_by_id(friendship.requester_id)
        if not requester:
            raise UserNotFound()
        try:
            removed_successfully = self.friend_repo.delete_friendship(friendship_id)
            if not removed_successfully:
                raise ServerError(
                    detail="Не удалось удалить запись о дружбе из-за внутренней ошибки сервера.",
                )
            other_user_id = None
            if friendship.requester_id == current_user_id:
                other_user_id = friendship.accepter_id
                notification_message = (
                    f"{requester.username} удалил(а) запись о вашей дружбе."
                )
            else:
                other_user_id = friendship.requester_id
                notification_message = (
                    f"{accepter.username} удалил(а) запись о вашей дружбе."
                )

            if other_user_id:
                self.notify_repo.add_notification(
                    user_id=other_user_id,  # Уведомление для "другой" стороны
                    notification_type=NotificationType.FRIENDSHIP_DELETED,  # Новый тип уведомления
                    message=notification_message,
                    sender_id=current_user_id,  # Тот, кто удалил
                    related_object_id=friendship.id,  # ID записи о дружбе
                )
            target_user_id_for_notification = (
                str(friendship.requester_id)
                if friendship.accepter_id == current_user_id
                else str(friendship.accepter_id)
            )

            notification_data = {
                "action": "friendship_deleted",
                "friendship_id": str(friendship.id),
                'user_id': str(target_user_id_for_notification),
                "deleted_by": str(current_user_id),
                "detail": f"Запись о дружбе с пользователем {current_user_id} удалена.",
            }
            await self.notify_service.send_mesasge_for_user(notification_data)
            return {"action": "delete friendship", "status": "success"}
        except Exception:
            logger.error(
                f"FriendshipService: Непредвиденная ошибка при отклонении запроса на дружбу {friendship_id} пользователем .",
                exc_info=True,
            )
            raise ServerError(
                detail="Не удалось отклонить запрос на дружбу из-за внутренней ошибки сервера.",
            )
