from abc import ABC,abstractmethod
import uuid
from app.schemas.entity import MemberRoomEntity,RoomEntity


class ABCMemberRoomAssociationRepository(ABC):
    """
    Абстрактный репозиторий для работы с участниками комнаты.
    """
    
    @abstractmethod
    def add_member(self,user_id: uuid.UUID,room_id: uuid.UUID,role: str) -> MemberRoomEntity:
        """
        Добавляет пользователя в комнату (создает запись о членстве).
        """
        raise NotImplementedError()

    @abstractmethod
    def remove_member(self,user_id: uuid.UUID, room_id: uuid.UUID) -> bool:
        """
        Удаляет пользователя из комнаты (удаляет запись о членстве).
        """
        raise NotImplementedError()

    @abstractmethod
    def get_association_by_ids(self, user_id: uuid.UUID, room_id: uuid.UUID) -> MemberRoomEntity | None:
        """
        Получает запись об ассоциации (членстве) по ID пользователя и ID комнаты.
        """
        raise NotImplementedError()

    @abstractmethod
    def get_members_by_room_id(self, room_id: uuid.UUID) -> list[MemberRoomEntity]:
        """
        Получает список объектов User, которые являются участниками данной комнаты.
        """
        raise NotImplementedError()

    @abstractmethod
    def get_rooms_by_user_id(self, user_id: uuid.UUID) -> list[RoomEntity]:
        """
        Получает список комнат пользователя
        """
        raise NotImplementedError()

    @abstractmethod
    def update_role(self,room_id: uuid.UUID,user_id: uuid.UUID,role: str) -> MemberRoomEntity | None:
        """
        Обновляет роль члена комнаты в базе данных.
        """
        raise NotImplementedError()

    @abstractmethod
    def get_member_room_association(self, room_id: uuid.UUID, user_id: uuid.UUID) -> MemberRoomEntity | None:
        """
        Получает запись об участии пользователя в конкретной комнате.
        Загружает отношения user и room.
        """
        raise NotImplementedError()