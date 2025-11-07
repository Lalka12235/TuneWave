from abc import ABC,abstractmethod
import uuid
from app.schemas.entity import FriendshipEntity
from app.schemas.enum import FriendshipStatus
from datetime import datetime



class ABCFriendshipRepository(ABC):
    """
    Абстрактный репозиторий для работы с дружбой.
    """

    @abstractmethod
    def get_friendship_by_id(self,friendship_id: uuid.UUID) -> FriendshipEntity | None:
        """
        Получает запись о дружбе по её ID.
        Загружает отношения requester и accepter для удобства.
        """
        raise NotImplementedError()

    @abstractmethod
    def get_friendship_by_users(self,user1_id: uuid.UUID,user2_id: uuid.UUID) -> FriendshipEntity | None:
        """
        Получает запись о дружбе между двумя конкретными пользователями,
        независимо от того, кто отправитель, а кто получатель.
        Загружает отношения requester и accepter.
        """
        raise NotImplementedError()

    @abstractmethod
    def get_user_friends(self,user_id: uuid.UUID) -> list[FriendshipEntity]:
        """
        Получает список всех принятых друзей для указанного пользователя.
        Загружает отношения requester и accepter.
        """
        raise NotImplementedError()

    @abstractmethod
    def get_sent_requests(self,requester_id: uuid.UUID) -> list[FriendshipEntity]:
        """
        Получает список всех запросов на дружбу, отправленных указанным пользователем,
        которые находятся в статусе PENDING.
        Загружает отношение accepter.
        """
        raise NotImplementedError()

    @abstractmethod
    def get_received_requests(self,accepter_id: uuid.UUID) -> list[FriendshipEntity]:
        """
        Получает список всех запросов на дружбу, полученных указанным пользователем,
        которые находятся в статусе PENDING.
        Загружает отношение requester.
        """
        raise NotImplementedError()

    @abstractmethod
    def add_friend_requet(self,requester_id: uuid.UUID,accepter_id: uuid.UUID) -> FriendshipEntity:
        """
        Создает новый запрос на дружбу со статусом PENDING.
        """
        raise NotImplementedError()
    
    @abstractmethod
    def update_friendship_status(self,friendship_id: uuid.UUID,new_status: FriendshipStatus,accepted_at: datetime | None = None) -> bool:
        """
        Обновляет статус существующего запроса на дружбу.
        """
        raise NotImplementedError()
    
    @abstractmethod
    def delete_friendship(self,friendship_id: uuid.UUID) -> bool:
        """
        Удаляет запись о дружбе (или запрос) по её ID.
        """
        raise NotImplementedError()