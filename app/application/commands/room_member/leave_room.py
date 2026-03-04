import uuid

from app.domain.entity import UserEntity
from app.domain.interfaces.member_room_association import MemberRoomAssociationGateway

from app.infrastructure.ws.manager_notify_service import NotifyService

from app.domain.exceptions.exception import ServerError
from app.domain.exceptions.room_exception import UserInRoomError

class LeaveRoom:
    def __init__(
        self,
        member_room_repo: MemberRoomAssociationGateway,
        notify_service: NotifyService
    ):
        self.member_room_repo = member_room_repo
        self.notify_service = notify_service

    async def leave_room(self, room_id: uuid.UUID, user: UserEntity) -> dict[str, str] | None:
        """
        Пользователь покидает комнату.
        """
        existing_association = self.member_room_repo.get_association_by_ids(
            user.id, room_id
        )
        if not existing_association:
            raise UserInRoomError(
                detail="Вы не являетесь участником этой комнаты.",
            )
        room = self.room_repo.get_room_by_id(room_id)
        try:
            room_name_for_message = room.name
            deleted_successfully = self.member_room_repo.remove_member(user.id, room_id)
            
            await self.notify_service.send_mesasge_for_user(
                action="leave_room",
                room_id=room_id,
                user_id=user.id,
                username=user.username,
                detail=f"Вы вышли из комнате{room_name_for_message}"
            )
            await self.notify_service.send_message_for_room(
                action="leave_room",
                room_id=room_id,
                user_id=user.id,
                username=user.username,
                detail=f"{user.username} вышел из комнате"
            )
            
            if deleted_successfully:
                return {
                    "status": "success",
                    "detail": f"Вы успешно покинули комнату с ID: {room_id}.",
                    "user_id": str(user.id),
                    "room_id": str(room_id),
                }
        except Exception as e:
            raise ServerError(
                detail=f"Не удалось покинуть комнату.{e}",
            )