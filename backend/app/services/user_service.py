import uuid

from infrastructure.celery.tasks import send_email_task
from jwt import exceptions

from app.config.settings import settings
from app.logger.log_config import logger
from app.models.user import User
from app.repositories.ban_repo import BanRepository
from app.repositories.user_repo import UserRepository
from app.schemas.user_schemas import (
    GoogleOAuthData,
    SpotifyOAuthData,
    Token,
    UserCreate,
    UserResponse,
    UserUpdate,
)

from app.services.mappers.user_mapper import UserMapper

from app.exceptions.user_exception import (
    UserAlrediExist,
    UserNotFound,
    ServerError,
    UserNotPermission,
    UserNotAuthorized,
    AvatarFyleType,
    FileExceedsSize,
    
)   


class UserService:

    def __init__(
        self,
        user_repo: UserRepository,
        ban_repo: BanRepository,
        user_mapper: UserMapper,
    ):
        self.user_repo = user_repo
        self.ban_repo = ban_repo
        self.user_mapper = user_mapper

    def _check_for_existing_user_and_raise_if_found(
        self,
        email: str | None = None,
        google_id: str | None = None,
        spotify_id: str | None = None,
        exclude_user_id: uuid.UUID | None = None,
    ):
        """
        Вспомогательный метод для проверки существования пользователя по различным идентификаторам.
        Если пользователь найден (и его ID не совпадает с exclude_user_id), выбрасывает HTTPException (409 Conflict).
        """
        if email:
            user = self.user_repo.get_user_by_email(email)
            if user and (exclude_user_id is None or user.id != exclude_user_id):
                logger.warning(
                    f"Попытка создать/обновить пользователя: email '{email}' уже существует."
                )
                raise UserAlrediExist(
                    detail=f"Пользователь с email '{email}' уже существует."
                )

        if google_id:
            user = self.user_repo.get_user_by_google_id(google_id)
            if user and (exclude_user_id is None or user.id != exclude_user_id):
                logger.warning(
                    f"Попытка создать/обновить пользователя: Google ID '{google_id}' уже существует."
                )
                raise UserAlrediExist(
                    detail=f"Пользователь с Google ID '{google_id}' уже существует."
                )

        if spotify_id:
            user = self.user_repo.get_user_by_spotify_id(spotify_id)
            if user and (exclude_user_id is None or user.id != exclude_user_id):
                logger.warning(
                    f"Попытка создать/обновить пользователя: Spotify ID '{spotify_id}' уже существует."
                )
                raise UserAlrediExist(
                    detail=f"Пользователь с Spotify ID '{spotify_id}' уже существует."
                )

    async def get_user_by_id(self, user_id: uuid.UUID) -> UserResponse:
        """
        Получает пользователя по его уникальному ID.

        Args:
            db (Session): Сессия базы данных.
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
            db (Session): Сессия базы данных.
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
            db (Session): Сессия базы данных.
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
            db (Session): Сессия базы данных.
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

    async def create_user(self, user_data: UserCreate) -> UserResponse:
        """Создание пользователя

        Args:
            db (Session): Сессия базы данных.
            user_data (UserCreate): Данные для создания пользоателя

        Returns:
            UserResponse: Информация о создании
        """
        self._check_for_existing_user_and_raise_if_found(
            user_data.email, user_data.google_id, user_data.spotify_id
        )
        try:
            new_user = self.user_repo.create_user(user_data.model_dump())
            logger.info(
                f"Пользователь '{user_data.username}' ({new_user.id}) успешно зарегистрирован."
            )
            subject = "Добро пожаловать в TuneWave!"
            body = f"""
            Привет, {user_data.username}!

            Спасибо за регистрацию в TuneWave. Мы рады видеть тебя в нашем музыкальном сообществе.
            Начни создавать комнаты и делиться музыкой с друзьями!

            С уважением,
            Команда TuneWave
            """
            email_sent = (user_data.email, subject, body)
            if not email_sent:
                logger.warning(f"Сообщение на почту не отправилось {email_sent}")
                pass
        except Exception as e:
            logger.error(
                f"Ошибка при создании пользователя '{user_data.email}': {e}",
                exc_info=True,
            )
            raise ServerError(detail="Ошибка при создании пользователя")

        return self.user_mapper.to_response(new_user)

    async def update_user_profile(
        self, user_id: uuid.UUID, update_data: UserUpdate
    ) -> UserResponse:
        """
        Обновляет профиль пользователя.
        Включает проверку на уникальность email, если он изменяется.

        Args:
            db (Session): Сессия базы данных.
            user_id (uuid.UUID): ID пользователя, чей профиль обновляется.
            update_data (UserUpdate): Pydantic-модель с данными для обновления.

        Returns:
            UserResponse: Обновленный объект UserResponse.

        Raises:
            HTTPException: Если пользователь не найден (404) или новый email уже занят другим пользователем (409).
        """
        user = self.user_repo.get_user_by_id(user_id)
        if not user:
            logger.warning(
                f"Попытка обновить профиль несуществующего пользователя с ID '{user_id}'."
            )
            raise UserNotFound(detail="Пользователь не найден")

        data_to_update = update_data.model_dump(exclude_unset=True)
        try:
            updated_user = self.user_repo.update_user(user, data_to_update)
            logger.info(f"Профиль пользователя '{user_id}' успешно обновлен.")
        except Exception as e:
            logger.error(
                f"Ошибка при обновлении профиля пользователя '{user_id}': {e}",
                exc_info=True,
            )
            raise ServerError(detail="Ошибка при обновлении пользователя")

        return self.user_mapper.to_response(updated_user)

    def hard_delete_user(self, user_id: uuid.UUID) -> dict[str, str]:
        """_summary_

        Args:
            db (Session): Сессия базы данных.
            user_id (uuid.UUID): ID пользователя для физического удаления.

        Raises:
            HTTPException: Пользователь не найден(404)

        Returns:
            dict[str,Any]: Информация об удалении
        """
        user = self.user_repo.get_user_by_id(user_id)

        if not user:
            logger.warning(
                f"Попытка удалить несуществующего пользователя с ID '{user_id}'."
            )
            raise UserNotFound(detail="Пользователь не найден")
        try:
            _ = self.user_repo.hard_delete_user(user_id)
        except Exception as e:
            logger.error(
                f"Ошибка при физическом удалении пользователя '{user_id}': {e}",
                exc_info=True,
            )
            raise ServerError(detail="Ошибка при удаление пользователя")

        return {
            "detail": "delete user",
            "status": "success",
            "id": str(user_id),
        }

    async def load_avatar(
        self, user: User, content: bytes, content_type: str, filename: str
    ) -> UserResponse:
        """
        Загружает файл аватарки, сохраняет его и обновляет URL в профиле пользователя.

        Args:
            user (User): Объект текущего пользователя
            content (bytes): Содержимое файла в байтах
            content_type (str): MIME-тип файла
            filename (str): Имя загружаемого файла

        Raises:
            HTTPException: Если файл не соответствует требованиям (тип, размер)

        Returns:
            UserResponse: Обновленный объект пользователя с новым URL аватарки
        """
        allowed_types = ["image/jpeg", "image/png", "image/gif"]
        if content_type not in allowed_types:
            logger.warning(
                f"Загруженный файл аватара имеет недопустимый тип: '{content_type}'."
            )
            raise AvatarFyleType(
                detail="Изображение должно быть в формате JPEG, PNG или GIF",
            )

        if len(content) > settings.avatar.MAX_AVATAR_SIZE_BYTES:
            logger.warning(
                f"Размер загруженного файла аватара ({len(content)} байт) "
                f"превышает лимит ({settings.avatar.MAX_AVATAR_SIZE_BYTES} байт)."
            )
            raise FileExceedsSize(
                detail=f"Размер файла не должен превышать {settings.avatar.MAX_AVATAR_SIZE_BYTES // (1024*1024)}МБ",
            )

        file_extension = filename.split(".")[-1] if "." in filename else "png"
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        file_path = settings.avatar.AVATARS_STORAGE_DIR / unique_filename

        try:
            settings.avatar.AVATARS_STORAGE_DIR.mkdir(parents=True, exist_ok=True)

            with open(file_path, "wb") as f:
                f.write(content)

            new_avatar_url = f"{settings.BASE_URL}/avatars/{unique_filename}"
            updated_user = await self.update_user_profile(
                user.id, UserUpdate(avatar_url=new_avatar_url)
            )

            logger.info(
                f"Аватар пользователя '{user.id}' успешно загружен и обновлен. URL: {new_avatar_url}"
            )
            return updated_user

        except Exception as e:
            if file_path.exists():
                file_path.unlink()
            logger.error(
                f"Ошибка сервера при загрузке аватара для пользователя '{user.id}': {e}",
                exc_info=True,
            )
            raise ServerError(
                detail="Ошибка сервера при загрузке аватара",
            )
