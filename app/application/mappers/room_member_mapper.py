from app.domain.entity import MemberRoomEntity
from app.presentation.schemas.room_member_schemas import RoomMemberResponse
from app.application.mappers.user_mapper import UserMapper

class RoomMemberMapper:
    def __init__(self, user_mapper: UserMapper):
        self._user_mapper = user_mapper

    def to_response(self, member: MemberRoomEntity) -> RoomMemberResponse:
        return RoomMemberResponse(

        )