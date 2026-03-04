import uuid

from app.domain.entity import UserEntity
from app.domain.interfaces.member_room_association import MemberRoomAssociationGateway
from app.domain.interfaces.room_gateway import RoomGateway
from app.domain.interfaces.user_gateway import UserGateway

from app.domain.enum import Role

from app.infrastructure.ws.manager_notify_service import NotifyService

from app.domain.exceptions.exception import ServerError
from app.domain.exceptions.room_exception import (
    RoomNotFoundError,
    SelfInteractionError,
    UserNotInRoomError,
    RoomPermissionDeniedError,
)

class KickMember:
    def __init__(
        self,
        room_repo: RoomGateway,
        user_repo: UserGateway,
        member_room_repo: MemberRoomAssociationGateway,
        notify_service: NotifyService
    ):
        self.room_repo = room_repo
        self.user_repo = user_repo
        self.member_room_repo = member_room_repo
        self.notify_service = notify_service
    
    def _check_not_self(self, current_user_id: uuid.UUID, target_user_id: uuid.UUID) -> None:
        if current_user_id == target_user_id:
            raise SelfInteractionError(
                detail="Вы не можете выполнять действия самим с собой"
            )

    async def kick_member_from_room(
        self, room_id: uuid.UUID, user_id: uuid.UUID, current_user: UserEntity
    ) -> dict[str, str]:
        """
        Удаляет указанного пользователя из комнаты. 🚪

        Эту операцию могут выполнять только владелец или модератор комнаты.
        Модераторы не могут кикать владельцев или других модераторов.
        Пользователь не может кикнуть самого себя.
        """
        room = self.room_repo.get_room_by_id(room_id)
        if not room:
            raise RoomNotFoundError()

        current_user_association = self.member_room_repo.get_association_by_ids(
            current_user.id, room_id
        )
        if not current_user_association or current_user_association.role not in [
            Role.OWNER.value,
            Role.MODERATOR.value,
        ]:
            raise RoomPermissionDeniedError(
                detail="У вас нет прав для изменения ролей в этой комнате. Только владелец и модератор может это делать.",
            )

        target_user_association = self.member_room_repo.get_association_by_ids(
            user_id, room_id
        )
        target_user = self.user_repo.get_user_by_id(user_id)
        if not target_user_association:
            raise UserNotInRoomError(
                detail="Пользователь, которого вы пытаетесь кикнуть, не найден в этой комнате.",
            )
        self._check_not_self(current_user.id,user_id)
        if user_id == room.owner_id:
            raise RoomPermissionDeniedError(
                detail="Владельца нельяза кикнуть из комнаты.",
            )

        if current_user_association.role == Role.MODERATOR.value:
            if target_user_association.role == Role.MODERATOR.value:
                raise RoomPermissionDeniedError(detail="Нельзя кикнуть модератора")
            elif target_user_association.role == Role.OWNER.value:
                raise RoomPermissionDeniedError(detail="Нельзя кикнуть Владельца")

        try:
            msg_user = dict(action="user_kicked_from_room",
                kicked_user_id=user_id,
                kicked_username=target_user.username,
                room_id=str(room_id),
                moderator_id=str(current_user.id),
                detail=f"Вы были кикнуты из комнаты {room.name}",)
            
            msg_room = dict(action="user_kicked_from_room",
                kicked_user_id=user_id,
                kicked_username=target_user.username,
                room_id=str(room_id),
                moderator_id=str(current_user.id),
                detail=f"Пользователь {target_user.username} был кикнут из комнаты.",)
            self.member_room_repo.remove_member(user_id, room_id)

            await self.notify_service.send_mesasge_for_user(msg_user)
            await self.notify_service.send_message_for_room(msg_room)
            
            return {
                "action": "kick member",
                "status": "success",
                "user_id": user_id,
                "room_id": room_id,
            }
        except Exception as e:
            raise ServerError(
                detail=f"Ошибка сервера при кике пользователя: {e}",
            )