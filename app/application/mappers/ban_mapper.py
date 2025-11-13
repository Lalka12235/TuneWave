from app.domain.entity import BanEntity
from app.presentation.schemas.ban_schemas import BanResponse
from app.application.mappers.base_mapper import BaseMapper
from app.application.mappers.user_mapper import UserMapper

class BanMapper(BaseMapper):
    def __init__(self, user_mapper: UserMapper):
        self._user_mapper = user_mapper

    def to_response(self, ban: BanEntity) -> BanResponse:
        return BanResponse(
            id=ban.id,
            ban_user_id=ban.ban_user_id,
            room_id=ban.room_id,
            reason=ban.reason,
            ban_date=ban.ban_date,
            by_ban_user_id=ban.by_ban_user_id,
        )