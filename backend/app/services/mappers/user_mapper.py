from app.models import User
from app.schemas.user_schemas import UserResponse
from app.services.mappers.base_mapper import BaseMapper


class UserMapper(BaseMapper):
    def to_response(self, user: User) -> UserResponse:
        return UserResponse.model_validate(user)
