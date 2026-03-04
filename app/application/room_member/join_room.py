import uuid

from app.domain.entity import UserEntity,RoomEntity
from app.domain.interfaces.ban_gateway import BanGateway
from app.domain.interfaces.member_room_association import MemberRoomAssociationGateway
from app.domain.interfaces.room_gateway import RoomGateway

from app.domain.enum import Role

from app.presentation.auth.hash import verify_pass
from app.infrastructure.ws.manager_notify_service import NotifyService

from app.domain.exceptions.exception import ServerError
from app.domain.exceptions.room_exception import (
    RoomNotFoundError,
    UserInRoomError,
    InvalidRoomPasswordError,
    RoomPermissionDeniedError,
)
from app.domain.exceptions.ban_exception import UserBannedGlobal, UserBannedInRoom

class JoinRoom:
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
    
    def _verify_room_password(room: RoomEntity, password: str) -> bool:
        """
        Проверяет предоставленный пароль для приватной комнаты.
        """
        if not room.is_private or not room.password_hash:
            return False

        return verify_pass(password, room.password_hash)

    async def join_room(
        self, user: UserEntity, room_id: uuid.UUID, password: str | None = None
    ) -> RoomEntity:
        """
        Пользователь присоединяется к комнате.
        """
        room = self.room_repo.get_room_by_id(room_id)
        if not room:
            raise RoomNotFoundError()
        global_ban = self.ban_repo.is_user_banned_global(user.id)
        if global_ban:
            raise UserBannedGlobal()

        local_ban = self.ban_repo.is_user_banned_local(user.id, room_id)
        if local_ban:
            raise UserBannedInRoom()

        existing_association = self.member_room_repo.get_association_by_ids(
            user.id, room_id
        )
        if existing_association:
            raise UserInRoomError()

        if room.is_private:
            if not password or not self._verify_room_password(room, password):
                raise InvalidRoomPasswordError()

        current_members_count = len(
            self.member_room_repo.get_members_by_room_id(room_id)
        )
        if current_members_count >= room.max_members:
            raise RoomPermissionDeniedError(
                detail="Комната заполнена. Невозможно присоединиться."
            )
        try:
            self.member_room_repo.add_member(user.id, room_id, role=Role.MEMBER.value)

            await self.notify_service.send_mesasge_for_user(
                action="join_room",
                room_id=room_id,
                user_id=user.id,
                username=user.username,
                detail=f"Вы присоединились к комнате {room.name}",
            )
            await self.notify_service.send_message_for_room(
                action="join_room",
                room_id=room_id,
                user_id=user.id,
                username=user.username,
                detail=f"{user.username} присоединился к комнате",
            )

            return room
        except Exception as e:
            raise ServerError(detail=f"Не удалось присоединиться к комнате. {e}")