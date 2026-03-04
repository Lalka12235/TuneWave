import uuid
from app.config.log_config import logger
from app.domain.enum import NotificationType, FriendshipStatus
from app.domain.exceptions.user_exception import UserNotFound
from app.domain.interfaces.friendship_gateway import FriendshipGateway
from app.domain.interfaces.user_gateway import UserGateway
from app.domain.interfaces.notification_gateway import NotificationGateway
from app.infrastructure.ws.manager_notify_service import NotifyService

from app.domain.exceptions.exception import ServerError
from app.domain.exceptions.friendship_exception import (
    FriendshipNotFoundError,
    FriendshipPermissionError,
    FriendshipStateError,
)


class DeclineFriendRequest:
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

    async def decline_friend_request(
        self, friendship_id: uuid.UUID, current_accepter_id: uuid.UUID
    ) -> dict[str, str]:
        """
        Отклоняет ожидающий запрос на дружбу.
        """
        friendship = self.friend_repo.get_friendship_by_id(friendship_id)
        if not friendship:
            raise FriendshipNotFoundError()

        if friendship.accepter_id != current_accepter_id:
            raise FriendshipPermissionError(
                detail="У вас нет прав для отклонения этого запроса на дружбу.",
            )

        if friendship.status != FriendshipStatus.PENDING:
            raise FriendshipStateError(
                detail='Запрос на дружбу не находится в статусе "ожидает" или уже обработан.',
            )
        accepter = self.user_repo.get_user_by_id(current_accepter_id)
        if not accepter:
            raise UserNotFound()
        requester = self.user_repo.get_user_by_id(friendship.requester_id)
        if not requester:
            raise UserNotFound()

        try:
            self.friend_repo.update_friendship_status(
                friendship_id, FriendshipStatus.DECLINED
            )
            notification_data_requester = {
                "action": "friend_request_declined",
                "friendship_id": str(friendship.id),
                "accepter_id": str(current_accepter_id),
                "accepter_username": accepter.username,
                'requester_id':str(friendship.requester_id),
                "detail": f"Ваш запрос на дружбу к {accepter.username} отклонен.",
            }
            self.notify_repo.add_notification(
                user_id=friendship.requester_id,  # Уведомление для отправителя запроса
                notification_type=NotificationType.FRIEND_DECLINED,  # Тип уведомления
                message=f"{accepter.username} отклонил(а) ваш запрос на дружбу.",
                sender_id=current_accepter_id,  # Тот, кто отклонил
                related_object_id=friendship.id,
            )
            await self.notify_service.send_message_for_requester(notification_data_requester)
            return {"status": "success", "message": "Friend request accepted"}
        except Exception:
            logger.error(
                f"FriendshipService: Непредвиденная ошибка при отклонении запроса на дружбу {friendship_id} пользователем {current_accepter_id}.",
                exc_info=True,
            )
            raise ServerError(
                detail="Не удалось отклонить запрос на дружбу из-за внутренней ошибки сервера.",
            )