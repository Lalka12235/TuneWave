from abc import ABC,abstractmethod
import uuid
from app.schemas.entity import RoomTrackAssociationEntity


class ABCRoomTrackAssociationRepository(ABC):

    @abstractmethod
    def add_track_to_queue(
        self,
        room_id: uuid.UUID,
        track_id: uuid.UUID,
        order_in_queue: int,
        user_id: uuid.UUID,
) -> RoomTrackAssociationEntity:
        """Добавляет новый трек в очередь конкретной комнаты."""
        raise NotImplementedError()
    
    @abstractmethod
    def get_queue_for_room(self,room_id: uuid.UUID) -> list[RoomTrackAssociationEntity]:
        """Получает все треки, находящиеся в очереди данной комнаты, отсортированные по порядку."""
        raise NotImplementedError()

    @abstractmethod
    def remove_track_from_queue(self,room_id: uuid.UUID,track_id: uuid.UUID) -> bool:
        """Удаляет конкретный трек из очереди комнаты по room_id и track_id."""
        raise NotImplementedError()
    @abstractmethod
    def get_last_order_in_queue(self,room_id: uuid.UUID) -> int:
        """Определяет следующий доступный номер для нового трека в очереди."""
        raise NotImplementedError()

    @abstractmethod
    def get_association_by_id(self, association_id: uuid.UUID) -> RoomTrackAssociationEntity | None:
        """Получает ассоциацию трека с комнатой по её ID."""
        raise NotImplementedError()

    @abstractmethod
    def remove_track_from_queue_by_association_id(self, association_id: uuid.UUID) -> bool:
        """Удаляет трек из очереди по ID ассоциации."""
        raise NotImplementedError()

    @abstractmethod
    def get_association_by_room_and_track(self, room_id: uuid.UUID,track_id: uuid.UUID) -> RoomTrackAssociationEntity | None:
        """Получает ассоциацию трека с комнатой по её ID."""
        raise NotImplementedError()

    @abstractmethod
    def get_first_track_in_queue(self,room_id: uuid.UUID) -> RoomTrackAssociationEntity | None:
        """
        Получает первый трек в очереди комнаты
        """
        raise NotImplementedError()