from app.models import Ban
from app.schemas.ban_schemas import BanResponse
from app.services.mappers.base_mapper import BaseMapper
from app.services.mappers.user_mapper import UserMapper

class BanMapper(BaseMapper):
    def __init__(self, user_mapper: UserMapper):
        self._user_mapper = user_mapper

    def to_response(self, ban: Ban) -> BanResponse:
        return BanResponse(
            id=ban.id,
            banned_user=self._user_mapper.to_response(ban.banned_user),
            admin=self._user_mapper.to_response(ban.admin),
            reason=ban.reason,
            created_at=ban.created_at,
            expires_at=ban.expires_at
        )