from app.domain.interfaces.user_gateway import UserGateway
from app.domain.entity import UserEntity
import uuid
from app.domain.exceptions.user_exception import UserNotFound
from app.config.log_config import logger


class ReadUser:
    
    def __init__(self,user_repo: UserGateway):
        self.user_repo = user_repo
    
    async def get_user_by_id(self, user_id: uuid.UUID) -> UserEntity:
        """
        Получает пользователя по его уникальному ID.
        """
        user = self.user_repo.get_user_by_id(user_id)
        if not user:
            logger.warning(
                f"Запрос пользователя по ID: Пользователь '{user_id}' не найден."
            )
            raise UserNotFound(detail="Пользователь не найден")

        return user

    def get_user_by_email(self, email: str) -> UserEntity:
        """
        Получает пользователя по его email.
        """
        user = self.user_repo.get_user_by_email(email)
        if not user:
            logger.warning(
                f"Запрос пользователя по email: Пользователь с email '{email}' не найден."
            )
            raise UserNotFound(detail="Пользователь не найден")

        return user

    def get_user_by_spotify_id(self, spotify_id: str) -> UserEntity:
        """
        Получает пользователя по его Spotify ID.
        """
        user = self.user_repo.get_user_by_spotify_id(spotify_id)
        if not user:
            logger.warning(
                f"Запрос пользователя по Spotify ID: Пользователь с Spotify ID '{spotify_id}' не найден."
            )
            raise UserNotFound(detail="Пользователь не найден")

        return user

    def get_user_by_google_id(self, google_id: str) -> UserEntity:
        """
        Получает пользователя по его Google ID.
        """
        user = self.user_repo.get_user_by_google_id(google_id)
        if not user:
            logger.warning(
                f"Запрос пользователя по Google ID: Пользователь с Google ID '{google_id}' не найден."
            )
            raise UserNotFound(detail="Пользователь не найден")

        return user