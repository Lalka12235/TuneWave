import uuid

from app.config.log_config import logger
from app.domain.interfaces.ban_gateway import BanGateway
from app.domain.interfaces.user_gateway import UserGateway
from app.presentation.schemas.user_schemas import (
    UserResponse,
)
from app.application.mappers.user_mapper import UserMapper

from app.domain.exceptions.user_exception import (
    UserAlrediExist,
    UserNotFound,
) 
from typing import Any


class UserService:
    """
    Реализует бизнес логику для работы с пользователем
    """

    def __init__(
        self,
        user_repo: UserGateway,
        ban_repo: BanGateway,
        user_mapper: UserMapper,
    ):
        self.user_repo = user_repo
        self.ban_repo = ban_repo
        self.user_mapper = user_mapper

    async def get_user_by_id(self, user_id: uuid.UUID) -> UserResponse:
        """
        Получает пользователя по его уникальному ID.

        Args:
            user_id (uuid.UUID): Уникальный идентификатор пользователя.

        Raises:
            HTTPException: Если пользователь не найден (статус 404 NOT FOUND).

        Returns:
            UserResponse: Pydantic-модель с данными пользователя.
        """
        user = self.user_repo.get_user_by_id(user_id)
        if not user:
            logger.warning(
                f"Запрос пользователя по ID: Пользователь '{user_id}' не найден."
            )
            raise UserNotFound(detail="Пользователь не найден")

        return self.user_mapper.to_response(user)

    def get_user_by_email(self, email: str) -> UserResponse:
        """
        Получает пользователя по его email.

        Args:
            email (str): Email пользователя.

        Raises:
            HTTPException: Если пользователь не найден (статус 404 NOT FOUND).

        Returns:
            UserResponse: Pydantic-модель с данными пользователя.
        """
        user = self.user_repo.get_user_by_email(email)
        if not user:
            logger.warning(
                f"Запрос пользователя по email: Пользователь с email '{email}' не найден."
            )
            raise UserNotFound(detail="Пользователь не найден")

        return self.user_mapper.to_response(user)

    def get_user_by_spotify_id(self, spotify_id: str) -> UserResponse:
        """
        Получает пользователя по его Spotify ID.

        Args:
            spotify_id (str): Spotify ID пользователя.

        Raises:
            HTTPException: Если пользователь не найден (статус 404 NOT FOUND).

        Returns:
            UserResponse: Pydantic-модель с данными пользователя.
        """
        user = self.user_repo.get_user_by_spotify_id(spotify_id)
        if not user:
            logger.warning(
                f"Запрос пользователя по Spotify ID: Пользователь с Spotify ID '{spotify_id}' не найден."
            )
            raise UserNotFound(detail="Пользователь не найден")

        return self.user_mapper.to_response(user)

    def get_user_by_google_id(self, google_id: str) -> UserResponse:
        """
        Получает пользователя по его Google ID.

        Args:
            google_id (str): Google ID пользователя.

        Raises:
            HTTPException: Если пользователь не найден (статус 404 NOT FOUND).

        Returns:
            UserResponse: Pydantic-модель с данными пользователя.
        """
        user = self.user_repo.get_user_by_google_id(google_id)
        if not user:
            logger.warning(
                f"Запрос пользователя по Google ID: Пользователь с Google ID '{google_id}' не найден."
            )
            raise UserNotFound(detail="Пользователь не найден")

        return self.user_mapper.to_response(user)

    async def create_user(self, user_data: dict[str,Any]) -> UserResponse:
        """Создание пользователя

        Args:
            user_data (UserCreate): Данные для создания пользоателя

        Returns:
            UserResponse: Информация о создании
        """
        user = self.user_repo.get_user_by_email(user_data.get('email'))

        if user:
            logger.warning(
                f"Попытка создать/обновить пользователя: уже существует."
            )
            raise UserAlrediExist(detail="Пользователь уже существует")
        new_user = self.user_repo.create_user(user_data)
        logger.info(
            f"Пользователь '{user_data.get('username')}' ({new_user.id}) успешно зарегистрирован."
        )
        return self.user_mapper.to_response(new_user)

    async def update_user_profile(
        self, user_id: uuid.UUID, update_data: dict[str,Any]
    ) -> UserResponse:
        """
        Обновляет профиль пользователя.
        Включает проверку на уникальность email, если он изменяется.

        Args:
            user_id (uuid.UUID): ID пользователя, чей профиль обновляется.
            update_data (UserUpdate): Pydantic-модель с данными для обновления.

        Returns:
            UserResponse: Обновленный объект UserResponse.
        """
        updated_user = self.user_repo.update_user(user_id, update_data)
        logger.info(f"Профиль пользователя '{user_id}' успешно обновлен.")

        return self.user_mapper.to_response(updated_user)

    def hard_delete_user(self, user_id: uuid.UUID) -> dict[str, str]:
        """_summary_

        Args:
            user_id (uuid.UUID): ID пользователя для физического удаления.

        Raises:
            HTTPException: Пользователь не найден(404)

        """
        status_deleted = self.user_repo.hard_delete_user(user_id)

        return {
            "detail": "delete user",
            "status": status_deleted,
            "id": str(user_id),
        }