from app.models import Member_room_association
from app.schemas.room_member_schemas import RoomMemberResponse
from app.services.mappers.base_mapper import BaseMapper
from app.services.mappers.user_mapper import UserMapper

class RoomMemberMapper(BaseMapper):
    def __init__(self, user_mapper: UserMapper):
        self._user_mapper = user_mapper

    def to_response(self, member: Member_room_association) -> RoomMemberResponse:
        return RoomMemberResponse(
            id=member.id,
            user=self._user_mapper.to_response(member.user),
            room_id=member.room_id,
            role=member.role,
            joined_at=member.joined_at
        )