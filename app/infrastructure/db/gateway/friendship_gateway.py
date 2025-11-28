from sqlalchemy import select,delete,or_,and_,update
from sqlalchemy.orm import Session,joinedload
from app.infrastructure.db.models import Friendship
import uuid
from app.domain.enum import FriendshipStatus
from datetime import datetime
from app.domain.entity import FriendshipEntity
from app.domain.interfaces.friendship_gateway import FriendshipGateway


class SAFriendshipGateway(FriendshipGateway):
    """
    Репозиторий для выполнения операций CRUD над моделью Friendship.
    Отвечает за управление записями о дружбе и запросах на дружбу.
    """

    def __init__(self, db: Session):
        self._db = db

    
    def from_model_to_entity(self,model: Friendship) -> FriendshipEntity:
        return FriendshipEntity(
            id=model.id,
            requester_id=model.requester_id,
            accepter_id=model.accepter_id,
            status=model.status,
            created_at=model.created_at,
            accepted_at=model.accepted_at,
        )

    
    def get_friendship_by_id(self,friendship_id: uuid.UUID) -> FriendshipEntity | None:
        """
        Получает запись о дружбе по её ID.
        Загружает отношения requester и accepter для удобства.

        Args:
            friendship_id (uuid.UUID): ID записи о дружбе.

        Returns:
            Optional[Friendship]: Объект Friendship или None, если не найден.
        """
        stmt = select(Friendship).where(
            Friendship.id == friendship_id,
        ).options(
            joinedload(Friendship.requester),
            joinedload(Friendship.accepter),
        )
        result = self._db.execute(stmt).scalar_one_or_none()
        return self.from_model_to_entity(result)
    

    
    def get_friendship_by_users(self,user1_id: uuid.UUID,user2_id: uuid.UUID) -> FriendshipEntity | None:
        """
        Получает запись о дружбе между двумя конкретными пользователями,
        независимо от того, кто отправитель, а кто получатель.
        Загружает отношения requester и accepter.

        Args:
            user1_id (uuid.UUID): ID первого пользователя.
            user2_id (uuid.UUID): ID второго пользователя.

        Returns:
            Optional[Friendship]: Объект Friendship (если существует), иначе None.
        """
        stmt = select(Friendship).where(
            or_(
                and_(Friendship.requester_id == user1_id, Friendship.accepter_id == user2_id),
                and_(Friendship.requester_id == user2_id, Friendship.accepter_id == user1_id)
            )
        ).options(
            joinedload(Friendship.requester),
            joinedload(Friendship.accepter),
        )
        result = self._db.execute(stmt).scalar_one_or_none()
        return self.from_model_to_entity(result)
    

    
    def get_user_friends(self,user_id: uuid.UUID) -> list[FriendshipEntity]:
        """
        Получает список всех принятых друзей для указанного пользователя.
        Загружает отношения requester и accepter.

        Args:
            user_id (uuid.UUID): ID пользователя, для которого ищутся друзья.

        Returns:
            List[Friendship]: Список объектов Friendship со статусом ACCEPTED.
        """
        stmt = select(Friendship).where(
            Friendship.status == FriendshipStatus.ACCEPTED,
            or_(
                Friendship.requester_id == user_id,
                Friendship.accepter_id == user_id,
            )
        ).options(
            joinedload(Friendship.requester),
            joinedload(Friendship.accepter),
        )
        result = self._db.execute(stmt).scalars().all()
        return result
    

    
    def get_sent_requests(self,requester_id: uuid.UUID) -> list[FriendshipEntity]:
        """
        Получает список всех запросов на дружбу, отправленных указанным пользователем,
        которые находятся в статусе PENDING.
        Загружает отношение accepter.

        Args:
            requester_id (uuid.UUID): ID пользователя, который отправил запросы.

        Returns:
            List[Friendship]: Список объектов Friendship со статусом PENDING.
        """
        stmt = select(Friendship).where(
            Friendship.requester_id == requester_id,
            Friendship.status == FriendshipStatus.PENDING,
        ).options(
            joinedload(Friendship.accepter),
        )
        result = self._db.execute(stmt).scalars().all()
        return result
    

    
    def get_received_requests(self,accepter_id: uuid.UUID) -> list[FriendshipEntity]:
        """
        Получает список всех запросов на дружбу, полученных указанным пользователем,
        которые находятся в статусе PENDING.
        Загружает отношение requester.

        Args:
            accepter_id (uuid.UUID): ID пользователя, который получил запросы.

        Returns:
            List[Friendship]: Список объектов Friendship со статусом PENDING.
        """
        stmt = select(Friendship).where(
            Friendship.status == FriendshipStatus.PENDING,
            Friendship.accepter_id == accepter_id,
        ).options(
            joinedload(Friendship.requester),
        )
        result = self._db.execute(stmt).scalars().all()
        return result



    
    def add_friend_requet(self,requester_id: uuid.UUID,accepter_id: uuid.UUID) -> FriendshipEntity:
        """
        Создает новый запрос на дружбу со статусом PENDING.

        Args:
            requester_id (uuid.UUID): ID пользователя, который отправляет запрос.
            accepter_id (uuid.UUID): ID пользователя, который получает запрос.

        Returns:
            Friendship: Созданный объект Friendship.
        """
        new_friendship = Friendship(
            requester_id=requester_id,
            accepter_id=accepter_id,
        )
        self._db.add(new_friendship)
        self._db.flush()
        return self.from_model_to_entity(new_friendship)
    
    
    
    def update_friendship_status(self,friendship_id: uuid.UUID,new_status: FriendshipStatus,accepted_at: datetime | None = None) -> bool:
        """
        Обновляет статус существующего запроса на дружбу.

        Args:
            friendship_id (uuid.UUID): ID записи о дружбе.
            new_status (FriendshipStatus): Новый статус (ACCEPTED или DECLINED).

        Returns:
            Optional[Friendship]: Обновленный объект Friendship или None, если не найден.
        """
        stmt = update(Friendship).where(
            Friendship.id == friendship_id,
        ).values(status=new_status,accepted_at=accepted_at)
        result = self._db.execute(stmt)
        return result.rowcount > 0
    

    
    def delete_friendship(self,friendship_id: uuid.UUID) -> bool:
        """
        Удаляет запись о дружбе (или запрос) по её ID.

        Args:
            friendship_id (uuid.UUID): ID записи о дружбе для удаления.

        Returns:
            bool: True, если запись была успешно удалена, иначе False.
        """
        stmt = delete(Friendship).where(
            Friendship.id == friendship_id,
        )
        result = self._db.execute(stmt)
        return result.rowcount > 0