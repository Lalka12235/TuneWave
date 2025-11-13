from app.infrastructure.db.models import User
from app.presentation.schemas.user_schemas import UserResponse
from app.application.mappers.base_mapper import BaseMapper


class UserMapper(BaseMapper):
    def to_response(self, user: User) -> UserResponse:
        return UserResponse.model_validate(user)
