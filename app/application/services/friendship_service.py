import json
import uuid
from datetime import datetime

from app.config.log_config import logger
from app.domain.enum import NotificationType, FriendshipStatus
from app.domain.exceptions.user_exception import UserNotFound
from app.domain.interfaces.friendship_gateway import FriendshipGateway
from app.domain.interfaces.user_gateway import UserGateway
from app.presentation.schemas.friendship_schemas import FriendshipResponse
from app.domain.interfaces.notification_gateway import NotificationGateway
from app.infrastructure.ws.connection_manager import manager
from app.application.mappers.friendship_mapper import FriendshipMapper

from app.domain.exceptions.exception import ServerError
from app.domain.exceptions.friendship_exception import (
    RequesterNotFoundError,
    ReceiverNotFoundError,
    SelfFriendshipError,
    PendingRequestError,
    ExistingFriendshipError,
    FriendshipNotFoundError,
    FriendshipPermissionError,
    FriendshipStateError,
)


class FriendshipService:
    """
    Реализует бизнес логику для работы с дружбой
    """

    def __init__(
        self,
        friend_repo: FriendshipGateway,
        notify_repo: NotificationGateway,
        user_repo: UserGateway,
        friendship_mapper: FriendshipMapper,
    ):
        self.friend_repo = friend_repo
        self.notify_repo = notify_repo
        self.user_repo = user_repo
        self.friendship_mapper = friendship_mapper

    def get_my_fridns(self, user_id: uuid.UUID) -> list[FriendshipResponse]:
        """
        Получает список всех принятых друзей для указанного пользователя.

        Args:
            user_id (uuid.UUID): ID пользователя, для которого ищутся друзья.

        Returns:
            List[FriendshipResponse]: Список объектов FriendshipResponse со статусом ACCEPTED.
        """
        friendships = self.friend_repo.get_user_friends(user_id)
        if not friendships:
            return []

        return [
            self.friendship_mapper.to_response(friendship) for friendship in friendships
        ]

    async def get_my_sent_requests(
        self, user_id: uuid.UUID
    ) -> list[FriendshipResponse]:
        """
        Получает список всех запросов на дружбу, отправленных указанным пользователем,
        которые находятся в статусе PENDING.

        Args:
            user_id (uuid.UUID): ID пользователя, который отправил запросы.

        Returns:
            List[FriendshipResponse]: Список объектов FriendshipResponse со статусом PENDING.
        """
        requests = self.friend_repo.get_sent_requests(user_id)
        if not requests:
            return []

        return [self.friendship_mapper.to_response(request) for request in requests]

    async def get_my_received_requests(
        self, user_id: uuid.UUID
    ) -> list[FriendshipResponse]:
        """
        Получает список всех запросов на дружбу, полученных указанным пользователем,
        которые находятся в статусе PENDING.

        Args:
            user_id (uuid.UUID): ID пользователя, который получил запросы.

        Returns:
            List[FriendshipResponse]: Список объектов FriendshipResponse со статусом PENDING.
        """
        requests = self.friend_repo.get_received_requests(user_id)
        if not requests:
            return []

        return [self.friendship_mapper.to_response(request) for request in requests]

    async def send_friend_request(
        self, requester_id: uuid.UUID, accepter_id: uuid.UUID
    ) -> FriendshipResponse:
        """
        Отправляет новый запрос на дружбу.

        Args:
            requester_id (uuid.UUID): ID пользователя, который отправляет запрос.
            accepter_id (uuid.UUID): ID пользователя, которому отправляется запрос.

        Returns:
            FriendshipResponse: Объект FriendshipResponse, представляющий созданный запрос.
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
            await manager.send_personal_message(
                json.dumps(notification_data), str(accepter_id)
            )
            return self.friendship_mapper.to_response(friendship)
        except Exception:
            logger.error(
                f"FriendshipService: Непредвиденная ошибка при отправке заявки на дружбу от {requester_id} к {accepter_id}.",
                exc_info=True,
            )
            raise ServerError(
                detail="Не удалось отправить запрос на дружбу из-за внутренней ошибки сервера.",
            )

    async def accept_friend_request(
        self, friendship_id: uuid.UUID, current_accepter_id: uuid.UUID
    ) -> dict[str, str]:
        """
        Принимает ожидающий запрос на дружбу.

        Args:
            friendship_id (uuid.UUID): ID записи о дружбе.
            current_accepter_id (uuid.UUID): ID текущего пользователя, который принимает запрос.

        Returns:
            FriendshipResponse: Объект FriendshipResponse, представляющий принятую дружбу.

        """
        friendship = self.friend_repo.get_friendship_by_id(friendship_id)
        if not friendship:
            raise FriendshipNotFoundError()

        if friendship.accepter_id != current_accepter_id:
            raise FriendshipPermissionError(
                detail="У вас нет прав для принятия этого запроса на дружбу.",
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
                friendship_id, FriendshipStatus.ACCEPTED, datetime.utcnow()
            )
            notification_data_requester = {
                "action": "friend_request_accepted",
                "friendship_id": str(friendship.id),
                "accepter_id": str(current_accepter_id),
                "accepter_username": accepter.username,
                "detail": f"Ваш запрос на дружбу к {accepter.username} принят. Вы теперь друзья!",
            }
            self.notify_repo.add_notification(
                user_id=friendship.requester_id,
                notification_type=NotificationType.FRIEND_ACCEPTED,
                message=f"{accepter.username} принял(а) ваш запрос на дружбу.",
                sender_id=current_accepter_id,  # Тот, кто принял
                related_object_id=friendship.id,
            )
            self.notify_repo.add_notification(
                user_id=current_accepter_id,
                notification_type=NotificationType.FRIEND_ACCEPTED,
                message=f"Вы приняли запрос на дружбу от {requester.username}. Теперь вы друзья!",
                sender_id=friendship.requester_id,  # Тот, кто отправил
                related_object_id=friendship.id,
            )
            notification_data_accepter = {
                "action": "friend_request_accepted",
                "friendship_id": str(friendship.id),
                "requester_id": str(friendship.requester_id),
                "requester_username": requester.username,
                "detail": f"Вы приняли запрос на дружбу от {requester.username}. Вы теперь друзья!",
            }

            await manager.send_personal_message(
                json.dumps(notification_data_accepter), str(current_accepter_id)
            )
            await manager.send_personal_message(
                json.dumps(notification_data_requester), str(friendship.requester_id)
            )

            return {"status": "success", "message": "Дружба принята"}
        except Exception:
            logger.error(
                "RoomService: Неизвестная ошибка при приглашении пользователя "
                "в комнату .",
                exc_info=True,
            )
            raise ServerError(
                detail="Не удалось создать уведомление из-за внутренней ошибки сервера.",
            )

    async def decline_friend_request(
        self, friendship_id: uuid.UUID, current_accepter_id: uuid.UUID
    ) -> dict[str, str]:
        """
        Отклоняет ожидающий запрос на дружбу.

        Args:
            friendship_id (uuid.UUID): ID записи о дружбе.
            current_accepter_id (uuid.UUID): ID текущего пользователя, который отклоняет запрос.

        Returns:
            FriendshipResponse: Объект FriendshipResponse, представляющий отклоненный запрос.
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
                "detail": f"Ваш запрос на дружбу к {accepter.username} отклонен.",
            }
            self.notify_repo.add_notification(
                user_id=friendship.requester_id,  # Уведомление для отправителя запроса
                notification_type=NotificationType.FRIEND_DECLINED,  # Тип уведомления
                message=f"{accepter.username} отклонил(а) ваш запрос на дружбу.",
                sender_id=current_accepter_id,  # Тот, кто отклонил
                related_object_id=friendship.id,
            )
            await manager.send_personal_message(
                json.dumps(notification_data_requester), str(friendship.requester_id)
            )
            return {"status": "success", "message": "Friend request accepted"}
        except Exception:
            logger.error(
                f"FriendshipService: Непредвиденная ошибка при отклонении запроса на дружбу {friendship_id} пользователем {current_accepter_id}.",
                exc_info=True,
            )
            raise ServerError(
                detail="Не удалось отклонить запрос на дружбу из-за внутренней ошибки сервера.",
            )

    async def delete_friendship(
        self, friendship_id: uuid.UUID, current_user_id: uuid.UUID
    ) -> dict[str, str]:
        """
        Отклоняет ожидающий запрос на дружбу.

        Args:
            friendship_id (uuid.UUID): ID записи о дружбе.
            current_accepter_id (uuid.UUID): ID текущего пользователя, который отклоняет запрос.

        Returns:
            FriendshipResponse: Объект FriendshipResponse, представляющий отклоненный запрос.
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
                "deleted_by": str(current_user_id),
                "detail": f"Запись о дружбе с пользователем {current_user_id} удалена.",
            }
            await manager.send_personal_message(
                json.dumps(notification_data), target_user_id_for_notification
            )
            return {"action": "delete friendship", "status": "success"}
        except Exception:
            logger.error(
                f"FriendshipService: Непредвиденная ошибка при отклонении запроса на дружбу {friendship_id} пользователем .",
                exc_info=True,
            )
            raise ServerError(
                detail="Не удалось отклонить запрос на дружбу из-за внутренней ошибки сервера.",
            )
