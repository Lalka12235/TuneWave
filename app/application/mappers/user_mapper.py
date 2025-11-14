from app.domain.entity import UserEntity
from app.presentation.schemas.user_schemas import UserResponse


class UserMapper:
    def to_response(self, user: UserEntity) -> UserResponse:
        return UserResponse.model_validate(user)
