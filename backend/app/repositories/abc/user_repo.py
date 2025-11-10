from abc import ABC,abstractmethod
import uuid
from app.schemas.entity import UserEntity

class UserRepository(ABC):
    """
    Абстрактный репозиторий для работы с пользователем.
    """
    
    @abstractmethod
    def get_user_by_id(self,user_id: uuid.UUID) -> UserEntity | None:
        """
        Получает пользователя по его уникальному ID.
        """
        raise NotImplementedError()

    @abstractmethod
    def get_user_by_email(self, email: str) -> UserEntity | None:
        """
        Получает пользователя по его email.
        """
        raise NotImplementedError()

    @abstractmethod
    def get_user_by_google_id(self, google_id: str) -> UserEntity | None:
        """
        Получает пользователя по его Google ID.
        """
        raise NotImplementedError()

    @abstractmethod
    def get_user_by_spotify_id(self, spotify_id: str) -> UserEntity | None:
        """
        Получает пользователя по его Spotify ID.
        """
        raise NotImplementedError()
    
    @abstractmethod
    def create_user(self, user_data: dict[str, str]) -> UserEntity:
        """
        Создает нового пользователя в базе данных.
        """
        raise NotImplementedError()
    
    @abstractmethod
    def update_user(self, user: UserEntity, update_data: dict[str, str]) -> UserEntity:
        """
        Обновляет существующего пользователя в базе данных.
        """
        raise NotImplementedError()
    
    @abstractmethod
    def hard_delete_user(self, user_id: uuid.UUID) -> bool:
        """
        Полностью удаляет пользователя из базы данных.
        Использовать с крайней осторожностью, так как данные будут безвозвратно утеряны.
        """
        raise NotImplementedError()