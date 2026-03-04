import uuid

from app.domain.entity import UserEntity
from app.domain.interfaces.member_room_association import MemberRoomAssociationGateway
from app.domain.interfaces.room_gateway import RoomGateway
from app.domain.interfaces.user_gateway import UserGateway

from app.domain.exceptions.room_exception import RoomNotFoundError


class ReadMember:
    def __init__(
        self,
        room_repo: RoomGateway,
        user_repo: UserGateway,
        member_room_repo: MemberRoomAssociationGateway,
    ):
        self.room_repo = room_repo
        self.user_repo = user_repo
        self.member_room_repo = member_room_repo
    

    async def get_room_members(self, room_id: uuid.UUID) -> list[UserEntity]:
        """
        Получает список участников комнаты.
        """
        room = self.room_repo.get_room_by_id(room_id)
        if not room:
            raise RoomNotFoundError()

        members = self.member_room_repo.get_members_by_room_id(room_id)
        if not members:
            return []

        return [self.user_repo.get_user_by_id(member.user_id) for member in members]