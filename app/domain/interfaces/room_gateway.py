from abc import ABC,abstractmethod
import uuid
from app.domain.entity import RoomEntity
from typing import Any


class RoomGateway(ABC):
    """
    Абстрактный репозиторий для работы с комнатами.
    """

    @abstractmethod
    def get_room_by_id(self, room_id: uuid.UUID) -> RoomEntity | None:
        """
        Получает комнату по ее уникальному идентификатору (ID).

        Args:
            room_id (uuid.UUID): ID комнаты для поиска.

        Returns:
            Room | None: Объект комнаты, если найден, иначе None.
        """
        raise NotImplementedError()
    
    @abstractmethod
    def get_room_by_name(self, name: str) -> RoomEntity | None:
        """
        Получает комнату по ее названию.

        Args:
            name (str): Название комнаты для поиска.

        Returns:
            Room | None: Объект комнаты, если найден, иначе None.
        """
        raise NotImplementedError()

    @abstractmethod
    def get_all_rooms(self) -> list[RoomEntity]:
        """
        Получает список всех комнат из базы данных.

        Returns:
            List[Room]: Список объектов Room.
        """
        raise NotImplementedError()

    @abstractmethod
    def create_room(self,room_data: dict[str, Any]) -> RoomEntity:
        """
        Создает новую комнату в базе данных.

        Args:
            room_data (Dict[str, Any]): Словарь с данными для создания комнаты.
                                        Должен содержать поля, соответствующие модели Room.

        Returns:
            Room: Созданный объект комнаты.
        """
        raise NotImplementedError()
    
    @abstractmethod
    def update_room(self,room: RoomEntity, update_data: dict[str,Any]) -> RoomEntity:
        """
        Обновляет существующую комнату в базе данных.

        Args:
            room (Room): Объект комнаты, который нужно обновить.
            update_data (Dict[str, Any]): Словарь с данными для обновления.

        Returns:
            Room: Обновленный объект комнаты.
        """
        raise NotImplementedError()

    @abstractmethod
    def delete_room(self, room_id: uuid.UUID) -> bool:
        """
        Удаляет комнату из базы данных по ее ID.

        Args:
            room_id (uuid.UUID): ID комнаты для удаления.

        Returns:
            bool: True, если комната была успешно удалена, иначе False.
        """
        raise NotImplementedError()
    
    @abstractmethod
    def get_active_rooms(self) -> list[RoomEntity]:
        """
        Возвращает список комнат, в которых сейчас играет музыка.
        Связанные объекты current_track загружаются одним запросом.
        """
        raise NotImplementedError()
    
    @abstractmethod
    def get_owner_room(self,room_id: uuid.UUID) -> RoomEntity | None:
        """_summary_

        Args:
            room_id (uuid.UUID): _description_

        Returns:
            User: _description_
        """
        raise NotImplementedError()