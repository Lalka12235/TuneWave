from typing import Any

from app.domain.entity.user import UserEntity
from app.domain.interfaces.member_room_association import MemberRoomAssociationGateway
from app.domain.interfaces.room_gateway import RoomGateway

from app.domain.enum import Role
from app.domain.entity import RoomEntity

from app.presentation.auth.hash import make_hash_pass
from app.infrastructure.ws.manager_notify_service import NotifyService

from app.domain.exceptions.room_exception import (
    RoomAlreadyExistsError,
    PrivateRoomRequiresPasswordError,
)


class CreateRoom:


    def __init__(
        self,
        room_repo: RoomGateway,
        member_room_repo: MemberRoomAssociationGateway,
        notify_service: NotifyService
    ):
        self.room_repo = room_repo
        self.member_room_repo = member_room_repo
        self.notify_service = notify_service


    async def create_room(self, room_data: dict[str,Any], owner: UserEntity) -> RoomEntity:
        """
        Создает новую комнату.
        Включает проверку уникальности имени и хэширование пароля.
        """
        room = self.room_repo.get_room_by_name(room_data.get('name'))
        if room:
            raise RoomAlreadyExistsError(
                detail=f"Комната с названием '{room_data.get('name')}' уже существует."
            )

        room_data["owner_id"] = owner.id

        if room_data.get('is_private'):
            if not room_data.get('password'):
                raise PrivateRoomRequiresPasswordError()
            room_data["password"] = make_hash_pass(room_data.get('password'))
        room_data["password_hash"] = None
        #if room_data.get('password'):
        #    raise PublicRoomCannotHavePasswordError()

        room_data.pop("password", None)
        
        new_room = self.room_repo.create_room(room_data)

        self.member_room_repo.add_member(
            owner.id, new_room.id, role=Role.OWNER.value
        )
        await self.notify_service.send_message_for_room(
            {"action": "room_created"}
        )

        return new_room