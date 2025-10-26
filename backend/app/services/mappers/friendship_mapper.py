from app.models import Friendship
from app.schemas.friendship_schemas import FriendshipResponse
from app.services.mappers.base_mapper import BaseMapper
from app.services.mappers.user_mapper import UserMapper

class FriendshipMapper(BaseMapper):
    def __init__(self, user_mapper: UserMapper):
        self._user_mapper = user_mapper

    def to_response(self, friendship: Friendship) -> FriendshipResponse:
        return FriendshipResponse(
            id=friendship.id,
            requester=self._user_mapper.to_response(friendship.requester),
            accepter=self._user_mapper.to_response(friendship.accepter),
            status=friendship.status,
            created_at=friendship.created_at,
            accepted_at=friendship.accepted_at
        )