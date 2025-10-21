from app.schemas.ban_schemas import BanResponse
from app.schemas.room_schemas import RoomMemberResponse, TrackInQueueResponse
from app.schemas.user_schemas import UserResponse
from app.models import Ban,Track,User,Member_room_association



def map_ban_to_response(ban: Ban) -> BanResponse:
    return BanResponse.model_validate(ban)

def map_track_to_response(track: Track) -> TrackInQueueResponse:
    return TrackInQueueResponse.model_validate(track)

def map_user_to_response(user: User) -> UserResponse:
    return UserResponse.model_validate(user)

def map_member_to_response(member: Member_room_association) -> RoomMemberResponse:
        """
        Вспомогательный метод для маппинга Member_room_association (включая загруженный User)
        в Pydantic RoomMemberResponse.
        """
        return RoomMemberResponse.model_validate(member)