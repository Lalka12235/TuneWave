import uuid

from app.domain.entity import UserEntity
from app.domain.interfaces.ban_gateway import BanGateway
from app.domain.interfaces.member_room_association import MemberRoomAssociationGateway
from app.domain.interfaces.room_gateway import RoomGateway

from app.domain.enum import Role

from app.infrastructure.ws.manager_notify_service import NotifyService

from app.domain.exceptions.exception import ServerError
from app.domain.exceptions.room_exception import (
    RoomNotFoundError,
    RoomPermissionDeniedError,
    SelfInteractionError,
)
from app.domain.exceptions.ban_exception import UserNotExistingBan

class UnbanUserInRoom:
    def __init__(
        self,
        room_repo: RoomGateway,
        member_room_repo: MemberRoomAssociationGateway,
        ban_repo: BanGateway,
        notify_service: NotifyService
    ):
        self.room_repo = room_repo
        self.member_room_repo = member_room_repo
        self.ban_repo = ban_repo
        self.notify_service = notify_service
            
    def _check_not_self(self, current_user_id: uuid.UUID, target_user_id: uuid.UUID) -> None:
        if current_user_id == target_user_id:
            raise SelfInteractionError(
                detail="Вы не можете выполнять действия самим с собой"
            )

    async def unban_user_from_room(
        self,
        room_id: uuid.UUID,
        target_user_id: uuid.UUID,
        current_user: UserEntity,
    ) -> dict[str, str]:
        """
        Снимает бан с пользователя в конкретной комнате.
        Только владелец комнаты может снимать баны.
        """
        room = self.room_repo.get_room_by_id(room_id)
        if not room:
            raise RoomNotFoundError()

        current_user_assoc = self.member_room_repo.get_association_by_ids(
            current_user.id, room_id
        )
        if not current_user_assoc or current_user_assoc.role != Role.OWNER.value:
            raise RoomPermissionDeniedError(
                detail="У вас нет прав для снятия банов в этой комнате. Только владелец может снимать баны.",
            )

        self._check_not_self(current_user.id,target_user_id)

        existing_ban_to_unban = self.ban_repo.is_user_banned_local(
            target_user_id, room_id
        )
        if not existing_ban_to_unban:
            raise UserNotExistingBan(
                detail="Пользователь не забанен в этой комнате.",
            )
        try:
            unbanned_successfully = self.ban_repo.remove_ban_local(
                target_user_id, room_id
            )

            if not unbanned_successfully:
                raise ServerError(
                    detail="Не удалось снять бан из-за внутренней ошибки сервера.",
                )

            await self.notify_service.send_mesasge_for_user({
                "action": "unban",
                "room_id": str(room_id),
                "user_id": str(target_user_id),
                "unbanned_by": str(current_user.id),
                "detail": f"Ваш бан в комнате{room.name} снят.",
            }
            )
            await self.notify_service.send_message_for_room(
                {
                "action": "unban",
                "room_id": str(room_id),
                "user_id": str(target_user_id),
                "unbanned_by": str(current_user.id),
                "detail": f"Бан пользователя {target_user_id} в комнате снят.",
                }
            )

            return {
                "status": "success",
                "detail": f"Бан с пользователя {target_user_id} в комнате {room_id} успешно снят.",
            }
        except Exception:
            raise ServerError(
                detail="Не удалось снять бан из-за внутренней ошибки сервера.",
            )