import uuid
from app.domain.entity.user import UserEntity
from app.domain.interfaces.room_gateway import RoomGateway

from app.domain.entity import RoomEntity

from app.domain.exceptions.room_exception import RoomNotFoundError


class ReadRoom:

    def __init__(
        self,
        room_repo: RoomGateway,
    ):
        self.room_repo = room_repo

    def get_room_by_id(self, room_id: uuid.UUID) -> RoomEntity:
        """
        Получает комнату по ее уникальному ID.
        """
        room = self.room_repo.get_room_by_id(room_id)
        if not room:
            raise RoomNotFoundError()

        return room

    def get_room_by_name(self, name: str) -> RoomEntity:
        """
        Получает комнату по ее названию.
        """
        room = self.room_repo.get_room_by_name(name)
        if not room:
            raise RoomNotFoundError()

        return room

    def get_all_rooms(self) -> list[RoomEntity]:
        """
        Получает список всех комнат из базы данных.
        """
        rooms_list = self.room_repo.get_all_rooms()

        return [room for room in rooms_list]
    
    def get_user_rooms(self, user: UserEntity) -> list[UserEntity]:
        """
        Получает список всех комнат, в которых состоит данный пользователь.
        """
        rooms = self.member_room_repo.get_rooms_by_user_id(user.id)
        return [room for room in rooms]