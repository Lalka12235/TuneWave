import uuid

from app.domain.entity.user import UserEntity
from app.domain.interfaces.room_gateway import RoomGateway


from app.domain.exceptions.room_exception import (
    RoomNotFoundError,
    RoomPermissionDeniedError,
)

class RoomService:


    def __init__(
        self,
        room_repo: RoomGateway,
    ):
        self.room_repo = room_repo

    def delete_room(self, room_id: uuid.UUID, owner: UserEntity) -> dict[str, str]:
        room = self.room_repo.get_room_by_id(room_id)
        if not room:
            raise RoomNotFoundError()

        if room.owner_id != owner.id:
            raise RoomPermissionDeniedError(
                detail="У вас нет прав для удаления этой комнаты.",
            )
        deleted_successfully = self.room_repo.delete_room(room_id)

        if deleted_successfully:
            return {
                "status": str(deleted_successfully),
                "detail": "Комната успешно удалена.",
                "id": str(room_id),
            }
        else:
            return {
                "status": str(deleted_successfully),
                "detail": "Комната не удалена.",
                "id": str(room_id),
            }