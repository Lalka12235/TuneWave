import uuid
from typing import Any

from app.domain.entity.room import RoomEntity
from app.domain.entity.user import UserEntity
from app.domain.interfaces.room_gateway import RoomGateway


from app.presentation.auth.hash import make_hash_pass

from app.domain.exceptions.room_exception import (
    RoomNotFoundError,
    RoomPermissionDeniedError,
)


class UpdateRoom:
    def __init__(
        self,
        room_repo: RoomGateway,
    ):
        self.room_repo = room_repo

    def update_room(
        self, room_id: uuid.UUID, update_data: dict[str,Any], current_user: UserEntity
    ) -> RoomEntity:
        """
        Обновляет существующую комнату.
        Только владелец комнаты может ее обновить.
        """
        room = self.room_repo.get_room_by_id(room_id)
        if not room:
            raise RoomNotFoundError()

        if room.owner_id != current_user.id:
            raise RoomPermissionDeniedError(
                detail="У вас нет прав для обновления этой комнаты.",
            )
            
        if "is_private" in update_data:
            if "password" in update_data and update_data["password"] is not None:
                update_data["password_hash"] = make_hash_pass(
                    update_data.pop("password")
                )
        else:
            update_data["password_hash"] = None

        updated_room_db = self.room_repo.update_room(room, update_data)

        return updated_room_db