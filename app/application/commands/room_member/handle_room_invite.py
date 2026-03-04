import uuid

from app.domain.entity import NotificationEntity
from app.domain.interfaces.ban_gateway import BanGateway
from app.domain.interfaces.member_room_association import MemberRoomAssociationGateway
from app.domain.interfaces.room_gateway import RoomGateway
from app.domain.interfaces.user_gateway import UserGateway

from app.domain.enum import NotificationType, Role
from app.presentation.schemas.notification_schemas import NotificationResponse

from app.domain.interfaces.notification_gateway import NotificationGateway

from app.infrastructure.ws.manager_notify_service import NotifyService

from app.domain.exceptions.exception import ServerError
from app.domain.exceptions.room_exception import (
    RoomNotFoundError,
    UserInRoomError,
    InvalidActionError,
)
from app.domain.exceptions.ban_exception import UserBannedInRoom
from app.domain.exceptions.notification_exception import NotificationNotPermission,NotificationTypeError,NotificationStateError

class HandleRoomInvite:
    def __init__(
        self,
        room_repo: RoomGateway,
        user_repo: UserGateway,
        member_room_repo: MemberRoomAssociationGateway,
        ban_repo: BanGateway,
        notify_repo: NotificationGateway,
        notify_service: NotifyService
    ):
        self.room_repo = room_repo
        self.user_repo = user_repo
        self.member_room_repo = member_room_repo
        self.ban_repo = ban_repo
        self.notify_repo = notify_repo
        self.notify_service = notify_service
    
    def _check_notification_owner(self,notification: NotificationEntity,current_user_id: uuid.UUID):
        if not notification.user_id == current_user_id:
            raise NotificationNotPermission(
                detail="Это уведомление принадлежит не вам"
            )
    def _check_notification_type(self,notification: NotificationEntity,expected_type: str): 
        if not notification.notification_type != expected_type:
            raise NotificationTypeError(
                detail=f"Это уведомление не является {expected_type}.",
            )
    def _check_notification_unread(self,notification: NotificationEntity):
        if not notification.is_read:
            raise NotificationStateError(
                detail="Это приглашение уже было обработано."
            )

    async def handle_room_invite_response(
        self,
        notification_id: uuid.UUID,
        current_user_id: uuid.UUID,
        action: NotificationType,
    ) -> NotificationResponse:
        """
        Обрабатывает ответ пользователя на приглашение в комнату (принять или отклонить).
        """
        notification = self.notify_repo.get_notification_by_id(notification_id)
        if not notification:
            raise RoomNotFoundError()

        self._check_notification_owner(notification,current_user_id)
        self._check_notification_type(notification, NotificationType.ROOM_INVITED.value)
        self._check_notification_unread(notification)

        room_id = notification.room_id
        inviter_id = notification.sender_id
        invited_user_id = notification.user_id

        try:
            room = self.room_repo.get_room_by_id(room_id)
            if not room:
                self.notify_repo.mark_notification_as_read(
                    notification_id, current_user_id
                )
                raise RoomNotFoundError(
                    detail="Комната, в которую вас пригласили, не найдена или удалена.",
                )

            inviter = self.user_repo.get_user_by_id(inviter_id) if inviter_id else None
            invited_user = self.user_repo.get_user_by_id(invited_user_id)

            if action == "accept":
                invited_member_in_room = (
                    self.member_room_repo.get_member_room_association(
                        room_id, invited_user_id
                    )
                )
                if invited_member_in_room:
                    self.notify_repo.mark_notification_as_read(
                        notification_id, current_user_id
                    )
                    raise UserInRoomError(
                        detail="Вы уже являетесь участником этой комнаты.",
                    )

                is_banned_local = self.ban_repo.is_user_banned_local(
                    invited_user_id, room_id
                )
                if is_banned_local:
                    self.notify_repo.mark_notification_as_read(
                        notification_id, current_user_id
                    )
                    raise UserBannedInRoom(
                        detail="Вы забанены в этой комнате и не можете присоединиться.",
                    )

                self.member_room_repo.add_member(invited_user_id, room_id, Role.MEMBER)

                self.notify_repo.mark_notification_as_read(
                    notification_id, current_user_id
                )

                await self.notify_service.send_message_for_room(
                {
                "action": "user_joined_room",
                    "room_id": str(room_id),
                    "user_id": str(invited_user_id),
                    "username": invited_user.username,
                    "detail": f"{invited_user.username} присоединился(ась) к комнате.",
                }
            )

                if inviter:
                    self.notify_repo.add_notification(
                        user_id=inviter_id,
                        notification_type=NotificationType.SYSTEM_MESSAGE,
                        message=f"{invited_user.username} принял(а) ваше приглашение в комнату {room.name}.",
                        sender_id=invited_user_id,
                        room_id=room_id,
                        related_object_id=room_id,
                    )

                self.notify_mapper.to_response(notification)

            elif action == "decline":
                self.notify_repo.mark_notification_as_read(
                    notification_id, current_user_id
                )

                if inviter:
                    self.notify_repo.add_notification(
                        user_id=inviter_id,
                        notification_type=NotificationType.SYSTEM_MESSAGE,
                        message=f"{invited_user.username} отклонил(а) ваше приглашение в комнату {room.name}.",
                        sender_id=invited_user_id,
                        room_id=room_id,
                        related_object_id=room_id,
                    )
                self.notify_mapper.to_response(notification)

            else:
                raise InvalidActionError(
                    detail='Недопустимое действие. Действие должно быть "accept" или "decline".',
                )
        except Exception:
            raise ServerError(
                detail="Не удалось обработать приглашение из-за внутренней ошибки сервера.",
            )