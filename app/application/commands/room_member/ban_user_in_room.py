import uuid

from app.domain.entity import UserEntity
from app.domain.interfaces.ban_gateway import BanGateway
from app.domain.interfaces.member_room_association import MemberRoomAssociationGateway
from app.domain.interfaces.room_gateway import RoomGateway
from app.domain.interfaces.user_gateway import UserGateway

from app.presentation.schemas.ban_schemas import BanCreate, BanResponse
from app.domain.enum import Role

from app.infrastructure.ws.manager_notify_service import NotifyService

from app.domain.exceptions.exception import ServerError
from app.domain.exceptions.room_exception import (
    RoomNotFoundError,
    RoomPermissionDeniedError,
    SelfInteractionError,
)
from app.domain.exceptions.ban_exception import UserBannedGlobal, UserBannedInRoom

class BanUserInRoom:
    def __init__(
        self,
        room_repo: RoomGateway,
        user_repo: UserGateway,
        member_room_repo: MemberRoomAssociationGateway,
        ban_repo: BanGateway,
        notify_service: NotifyService
    ):
        self.room_repo = room_repo
        self.user_repo = user_repo
        self.member_room_repo = member_room_repo
        self.ban_repo = ban_repo
        self.notify_service = notify_service

    def _check_not_self(self, current_user_id: uuid.UUID, target_user_id: uuid.UUID) -> None:
        if current_user_id == target_user_id:
            raise SelfInteractionError(
                detail="Вы не можете выполнять действия самим с собой"
            )

    async def ban_user_from_room(
        self,
        room_id: uuid.UUID,
        target_user_id: uuid.UUID,
        ban_data: BanCreate,
        current_user: UserEntity,
    ) -> BanResponse:
        """
        Банит пользователя в конкретной комнате или глобально.
        Только владелец комнаты может банить других пользователей.
        Модераторы НЕ могут банить.
        """
        room = self.room_repo.get_room_by_id(room_id)
        if not room:
            raise RoomNotFoundError()

        current_user_assoc = self.member_room_repo.get_association_by_ids(
            current_user.id, room_id
        )
        if not current_user_assoc or current_user_assoc.role != Role.OWNER.value:
            raise RoomPermissionDeniedError(
                detail="У вас нет прав для бана пользователей в этой комнате. Только владелец может банить.",
            )

        self._check_not_self(current_user.id,target_user_id)

        existing_global_ban = self.ban_repo.is_user_banned_global(target_user_id)
        if existing_global_ban:
            raise UserBannedGlobal()

        existing_local_ban = self.ban_repo.is_user_banned_local(
            target_user_id, room_id
        )
        if existing_local_ban:
            raise UserBannedInRoom()

        existing_member_association = self.member_room_repo.get_association_by_ids(
            target_user_id, room_id
        )
        if existing_member_association:
            removed_from_room = self.member_room_repo.remove_member(
                target_user_id, room_id
            )
            if not removed_from_room:
                raise ServerError(
                    detail="Не удалось подготовить пользователя к бану.",
                )
        try:
            new_ban_entry = self.ban_repo.add_ban(
                ban_user_id=target_user_id,
                room_id=room_id,
                reason=ban_data.reason,
                by_ban_user_id=current_user.id,
            )

            await self.notify_service.send_mesasge_for_user({
                "action": "ban",
                "room_id": str(room_id),
                "user_id": str(target_user_id),
                "banned_by": str(current_user.id),
                "reason": ban_data.reason if ban_data.reason else "не указана",
                "detail": f"Вы были забанены в комнате {room.name}.",
            }
            )
            await self.notify_service.send_message_for_room(
                {
                "action": "ban",
                "room_id": str(room_id),
                "user_id": str(target_user_id),
                "banned_by": str(current_user.id),
                "reason": ban_data.reason if ban_data.reason else "не указана",
                "detail": f"Пользователь {target_user_id} был забанен в комнате.",
                }
            )

            return self.ban_mapper.to_response(new_ban_entry)

        except Exception:
            raise ServerError(
                detail="Не удалось забанить пользователя из-за внутренней ошибки сервера.",
            )
