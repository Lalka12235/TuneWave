from abc import ABC,abstractmethod
import uuid
from app.schemas.entity import BanEntity


class ABCBanRepository(ABC):
    """
    Абстрактный репозиторий для работы с банами пользователей.
    """
    
    @abstractmethod
    def get_bans_by_admin(self,user_id: uuid.UUID) -> list[BanEntity]:
        """
        Получает список банов, выданных указанным пользователем (кто забанил).
        """
        raise NotImplementedError()
    
    @abstractmethod
    def get_bans_on_user(self,user_id: uuid.UUID) -> list[BanEntity]:
        """
        Получает список банов, полученных указанным пользователем (кого забанили).
        """
        raise NotImplementedError()

    @abstractmethod
    def add_ban(self,room_id: uuid.UUID,ban_user_id: uuid.UUID,reason: str,by_ban_user_id: uuid.UUID) -> BanEntity | None:
        """
        Добавляет новую запись о бане в базу данных.
        """
        raise NotImplementedError()
    
    @abstractmethod
    def remove_ban_local(self,room_id: uuid.UUID,ban_user_id: uuid.UUID) -> bool:
        """
        Удаляет запись о бане из базы данных.
        """
        raise NotImplementedError()
    
    @abstractmethod
    def remove_ban_global(self,ban_user_id: uuid.UUID) -> bool:
        """
        Снимает бан с платформы
        """
        raise NotImplementedError()
    
    @abstractmethod
    def is_user_banned_global(self, user_id: uuid.UUID) -> BanEntity | None:
        """
        Проверяет, забанен ли пользователь ГЛОБАЛЬНО (то есть, во всех комнатах).
        """
        raise NotImplementedError()
    
    @abstractmethod
    def is_user_banned_local(self, user_id: uuid.UUID,room_id: uuid.UUID) -> BanEntity | None:
        """
        Проверяет, забанен ли пользователь в КОНКРЕТНОЙ комнате.
        """
        raise NotImplementedError()