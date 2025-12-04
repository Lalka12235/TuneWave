from app.application.mappers.user_mapper import UserMapper
from app.config.log_config import logger
from app.config.settings import settings
from app.domain.entity import UserEntity
from app.domain.exceptions.exception import ServerError
from app.domain.exceptions.user_exception import AvatarFyleType, FileExceedsSize

from app.domain.interfaces.avatar_storage_gateway import AvatarStorageGateway
from app.domain.interfaces.user_gateway import UserGateway
from app.presentation.schemas.user_schemas import UserResponse


class AvatarStorageService:

    def __init__(self,avatar_storage: AvatarStorageGateway,user_repo: UserGateway,user_mapper: UserMapper):
        self.avatar_storage = avatar_storage
        self.user_repo = user_repo
        self.user_mapper = user_mapper

    def _check_allowed_typed_file(self,content_type: str) -> bool:
        allowed_types = ["image/jpeg", "image/png", "image/gif"]
        if content_type not in allowed_types:
            logger.warning(
                f"Загруженный файл аватара имеет недопустимый тип: '{content_type}'."
            )
            raise AvatarFyleType(
                detail="Изображение должно быть в формате JPEG, PNG или GIF",
            )
        return True

    def _check_exceeds_size(self,content: bytes) -> bool:
        if len(content) > settings.avatar.MAX_AVATAR_SIZE_BYTES:
            logger.warning(
                f"Размер загруженного файла аватара ({len(content)} байт) "
                f"превышает лимит ({settings.avatar.MAX_AVATAR_SIZE_BYTES} байт)."
            )
            raise FileExceedsSize(
                detail=f"Размер файла не должен превышать {settings.avatar.MAX_AVATAR_SIZE_BYTES // (1024*1024)}МБ",
            )
        return True

    async def load_avatar(
        self, user: UserEntity, content: bytes, content_type: str, filename: str
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
        self._check_allowed_typed_file(content_type)
        self._check_exceeds_size(content)

        try:

            new_avatar_url = self.avatar_storage.save_avatar(content,filename)

            updated_user = self.user_repo.update_user(
                user, {'avatar_url': new_avatar_url}
            )

            logger.info(
                f"Аватар пользователя '{user.id}' успешно загружен и обновлен. URL: {new_avatar_url}"
            )
            return self.user_mapper.to_response(updated_user)

        except Exception as e:
            logger.error(
                f"Ошибка сервера при загрузке аватара для пользователя '{user.id}': {e}",
                exc_info=True,
            )
            raise ServerError(
                detail="Ошибка сервера при загрузке аватара",
            )