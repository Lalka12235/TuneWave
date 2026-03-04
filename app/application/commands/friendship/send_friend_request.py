import uuid

from app.config.log_config import logger
from app.domain.enum import NotificationType, FriendshipStatus
from app.domain.interfaces.friendship_gateway import FriendshipGateway
from app.domain.interfaces.user_gateway import UserGateway
from app.domain.entity import FriendshipEntity
from app.domain.interfaces.notification_gateway import NotificationGateway
from app.infrastructure.ws.manager_notify_service import NotifyService

from app.domain.exceptions.exception import ServerError
from app.domain.exceptions.friendship_exception import (
    RequesterNotFoundError,
    ReceiverNotFoundError,
    SelfFriendshipError,
    PendingRequestError,
    ExistingFriendshipError,
)


class SendFriendRequest:
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

    async def send_friend_request(
        self, requester_id: uuid.UUID, accepter_id: uuid.UUID
    ) -> FriendshipEntity:
        """
        Отправляет новый запрос на дружбу.
        """
        if requester_id == accepter_id:
            raise SelfFriendshipError()

        req_user = self.user_repo.get_user_by_id(requester_id)
        if not req_user:
            raise RequesterNotFoundError()

        acc_user = self.user_repo.get_user_by_id(accepter_id)
        if not acc_user:
            raise ReceiverNotFoundError()

        friendship_by_user = self.friend_repo.get_friendship_by_users(
            requester_id, accepter_id
        )
        if friendship_by_user:
            if friendship_by_user.status == FriendshipStatus.PENDING:
                raise PendingRequestError()
            elif friendship_by_user.status == FriendshipStatus.ACCEPTED:
                raise ExistingFriendshipError()
            #elif friendship_by_user.status == FriendshipStatus.DECLINED:
            #    raise HTTPException(
            #        status_code=400,
            #        detail="Этот пользователь отклонил ваш предыдущий запрос.",
            #    )

        try:
            friendship = self.friend_repo.add_friend_requet(requester_id, accepter_id)
            self.notify_repo.add_notification(
                user_id=accepter_id,
                notification_type=NotificationType.FRIEND_REQUEST,
                message=f"Вам пришел новый запрос на дружбу от {req_user.username}.",
                sender_id=requester_id,
                related_object_id=friendship.id,
            )
            notification_data = {
                "action": "friend_request_received",
                "friendship_id": str(friendship.id),
                "requester_id": str(requester_id),
                "requester_username": req_user.username,
                "detail": f"Вы получили новый запрос на дружбу от {req_user.username}.",
            }
            await self.notify_service.send_message_for_requester(notification_data)
            return friendship
        except Exception:
            logger.error(
                f"FriendshipService: Непредвиденная ошибка при отправке заявки на дружбу от {requester_id} к {accepter_id}.",
                exc_info=True,
            )
            raise ServerError(
                detail="Не удалось отправить запрос на дружбу из-за внутренней ошибки сервера.",
            )