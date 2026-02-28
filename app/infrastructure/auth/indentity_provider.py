from app.infrastructure.redis.redis_service import RedisService
from app.application.services.session_service import SessionID
import uuid
from app.domain.entity.user import UserEntity
from app.domain.exceptions.user_exception import UserNotFound
from app.domain.interfaces.user_gateway import UserGateway


class IndentityProvider:

    def __init__(
        self,
        user_repo: UserGateway,
        redis_service: RedisService,
        session_id: SessionID = None,
    ) -> None:
        self.__session_id = session_id
        self.user_repo = user_repo
        self.redis = redis_service

    def get_current_user_id(self) -> uuid.UUID:
        key_session = f"session:{self.__session_id}"
        user_id = self.redis.get(key_session)
        if not user_id:
            return UserNotFound()

        return user_id

    def get_current_user(self) -> UserEntity:
        key_session = f"session:{self.__session_id}"
        user_id = self.redis.get(key_session)
        user = self.user_repo.get_user_by_id(user_id)
        if not user:
            return UserNotFound()

        return user

    @property.setter
    def set_session_id(self, session_id: SessionID) -> None:
        self.__session_id = session_id
