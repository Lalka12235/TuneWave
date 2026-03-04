import uuid

from app.config.log_config import logger
from app.domain.entity import UserEntity
from app.domain.interfaces.ban_gateway import BanGateway
from app.domain.interfaces.member_room_association import MemberRoomAssociationGateway
from app.domain.interfaces.room_gateway import RoomGateway
from app.domain.interfaces.user_gateway import UserGateway

from app.domain.enum import NotificationType, Role

from app.domain.interfaces.notification_gateway import NotificationGateway

from app.infrastructure.ws.manager_notify_service import NotifyService

from app.domain.exceptions.exception import ServerError
from app.domain.exceptions.room_exception import (
    RoomNotFoundError,
    UserInRoomError,
    RoomPermissionDeniedError,
    SelfInteractionError,
)
from app.domain.exceptions.ban_exception import UserBannedInRoom
from app.domain.exceptions.user_exception import UserNotFound

class SendRoomInvite:
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
            
    def _check_users_exist(self, inviter_id: uuid.UUID, invited_user_id: uuid.UUID) -> tuple[UserEntity,UserEntity]:
        inviter = self.user_repo.get_user_by_id(inviter_id)
        if not inviter:
            raise UserNotFound(detail="Приглашающий пользователь не найден")
        
        invited = self.user_repo.get_user_by_id(invited_user_id)
        if not invited:
            raise UserNotFound(detail="Приглашаемый пользователь не найден")
        
        return inviter, invited

    def _check_not_self(self, current_user_id: uuid.UUID, target_user_id: uuid.UUID) -> None:
        if current_user_id == target_user_id:
            raise SelfInteractionError(
                detail="Вы не можете выполнять действия самим с собой"
            )

    async def send_room_invite(
        self,
        room_id: uuid.UUID,
        inviter_id: uuid.UUID,
        invited_user_id: uuid.UUID,
    ) -> dict[str, str]:
        """
        Отправляет приглашение в комнату указанному пользователю.
        """
        room = self.room_repo.get_room_by_id(room_id)
        if not room:
            raise RoomNotFoundError()
        
        inviter,invited = self._check_users_exist(inviter_id,invited_user_id)

        self._check_not_self(inviter_id,invited_user_id)

        inviter_membership = self.member_room_repo.get_member_room_association(
            room_id, inviter_id
        )
        if not inviter_membership or inviter_membership.role not in [
            Role.OWNER.value,
            Role.MODERATOR.value,
        ]:
            raise RoomPermissionDeniedError(
                detail="У вас нет прав для приглашения пользователей в эту комнату. Только владельцы и модераторы могут это делать.",
            )

        invited_member_in_room = self.member_room_repo.get_member_room_association(
            room_id, invited_user_id
        )
        if invited_member_in_room:
            raise UserInRoomError()

        have_banned = self.ban_repo.is_user_banned_local(invited_user_id, room_id)
        if have_banned:
            raise UserBannedInRoom()

        try:
            self.notify_repo.add_notification(
                invited_user_id,
                NotificationType.ROOM_INVITED,
                message=f"{inviter.username} приглашает вас в комнату {room.name}.",
                sender_id=inviter_id,
                room_id=room_id,
                related_object_id=room_id,
            )
            logger.info(
                f"RoomService: уведомление успешно отправлено пользователю {invited_user_id} из комнаты {room_id}"
            )

            await self.notify_service.send_mesasge_for_user({
                "action": "room_invite_received",
                "room_id": str(room_id),
                "room_name": room.name,
                "inviter_id": str(inviter_id),
                "inviter_username": inviter.username,
                "detail": f"Вы получили приглашение в комнату {room.name} от {inviter.username}.",
            }
            )

            return {"status": "success", "detail": "Приглашение отправлено."}
        except Exception:
            logger.error(
                f"RoomService: Неизвестная ошибка при приглашении пользователя {invited_user_id} "
                f"в комнату {room_id}.",
                exc_info=True,
            )
            raise ServerError(
                detail="Не удалось создать уведомление из-за внутренней ошибки сервера.",
            )