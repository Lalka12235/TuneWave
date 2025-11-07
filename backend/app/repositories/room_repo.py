from app.models import Room,Member_room_association,RoomTrackAssociationModel
from sqlalchemy import select,delete
from sqlalchemy.orm import Session,joinedload
import uuid
from typing import Any
from app.schemas.entity import RoomEntity
from app.repositories.abc.room_repo import ABCRoomRepository


class RoomRepository(ABCRoomRepository):
    """
    Репозиторий для выполнения операций CRUD (Create, Read, Update, Delete)
    над моделью Room в базе данных.
    """

    def __init__(self, db: Session):
        self._db = db

    
    def from_model_to_entity(self,model: Room) -> RoomEntity:
        return RoomEntity(
            id=model.id,
            name=model.name,
            max_members=model.max_members,
            owner_id=model.owner_id,
            is_private=model.is_private,
            password_hash=model.password_hash,
            current_track_id=model.current_track_id,
            current_track_position_ms=model.current_track_position_ms,
            is_playing=model.is_playing,
            created_at=model.created_at,
            playback_host_id=model.playback_host_id,
            active_spotify_device_id=model.active_spotify_device_id,
            current_playing_track_association_id=model.current_playing_track_association_id
        )

    
    def get_room_by_id(self, room_id: uuid.UUID) -> RoomEntity | None:
        """
        Получает комнату по ее уникальному идентификатору (ID).

        Args:
            db (Session): Сессия базы данных SQLAlchemy.
            room_id (uuid.UUID): ID комнаты для поиска.

        Returns:
            Room | None: Объект комнаты, если найден, иначе None.
        """
        stmt = select(Room).options(
            joinedload(Room.owner),
            joinedload(Room.member_room).joinedload(Member_room_association.user),
            joinedload(Room.room_track).joinedload(RoomTrackAssociationModel.track)
        ).filter(Room.id == room_id)
        result = self._db.execute(stmt).unique().scalar_one_or_none()
        return self.from_model_to_entity(result)
    
    
    def get_room_by_name(self, name: str) -> RoomEntity | None:
        """
        Получает комнату по ее названию.

        Args:
            db (Session): Сессия базы данных SQLAlchemy.
            name (str): Название комнаты для поиска.

        Returns:
            Room | None: Объект комнаты, если найден, иначе None.
        """
        stmt = select(Room).options(
            joinedload(Room.owner),
            joinedload(Room.member_room).joinedload(Member_room_association.user),
            joinedload(Room.room_track).joinedload(RoomTrackAssociationModel.track)
        ).filter(Room.name == name)
        result = self._db.execute(stmt).unique().scalar_one_or_none()
        return self.from_model_to_entity(result)

    
    def get_all_rooms(self) -> list[RoomEntity]:
        """
        Получает список всех комнат из базы данных.

        Args:
            db (Session): Сессия базы данных SQLAlchemy.

        Returns:
            List[Room]: Список объектов Room.
        """
        stmt = select(Room).options(
            joinedload(Room.owner),
            joinedload(Room.member_room).joinedload(Member_room_association.user),
            joinedload(Room.room_track).joinedload(RoomTrackAssociationModel.track)
        )
        result = self._db.execute(stmt).unique().scalars().all()
        return self.from_model_to_entity(result)
    


    
    def create_room(self,room_data: dict[str, Any]) -> RoomEntity:
        """
        Создает новую комнату в базе данных.

        Args:
            db (Session): Сессия базы данных SQLAlchemy.
            room_data (Dict[str, Any]): Словарь с данными для создания комнаты.
                                        Должен содержать поля, соответствующие модели Room.

        Returns:
            Room: Созданный объект комнаты.
        """
        new_room = Room(**room_data)
        self._db.add(new_room)
        self._db.flush()
        self._db.refresh(new_room)
        return self.from_model_to_entity(new_room)
    
    
    def update_room(self,room: RoomEntity, update_data: dict[str,Any]) -> RoomEntity:
        """
        Обновляет существующую комнату в базе данных.

        Args:
            db (Session): Сессия базы данных SQLAlchemy.
            room (Room): Объект комнаты, который нужно обновить.
            update_data (Dict[str, Any]): Словарь с данными для обновления.

        Returns:
            Room: Обновленный объект комнаты.
        """
        for key,value in update_data.items():
            setattr(room,key,value)
        return self.from_model_to_entity(room)


    
    def delete_room(self, room_id: uuid.UUID) -> bool:
        """
        Удаляет комнату из базы данных по ее ID.

        Args:
            db (Session): Сессия базы данных SQLAlchemy.
            room_id (uuid.UUID): ID комнаты для удаления.

        Returns:
            bool: True, если комната была успешно удалена, иначе False.
        """
        stmt = delete(Room).where(Room.id == room_id)
        result = self._db.execute(stmt)
        return result.rowcount > 0
    

    
    def get_active_rooms(self) -> list[RoomEntity]:
        """
        Возвращает список комнат, в которых сейчас играет музыка.
        Связанные объекты current_track загружаются одним запросом.
        """
        stmt = select(Room).where(
            Room.is_playing,
        ).options(
            joinedload(Room.room_track),
        )
        result = self._db.execute(stmt).scalars().all()
        return self.from_model_to_entity(result)
    

    
    def get_owner_room(self,room_id: uuid.UUID) -> RoomEntity | None:
        """_summary_

        Args:
            db (Session): _description_
            room_id (uuid.UUID): _description_

        Returns:
            User: _description_
        """
        stmt = select(Room).where(
            Room.id == room_id,
        ).options(
            joinedload(Room.owner),
        )
        result = self._db.execute(stmt).scalar_one_or_none()
        return self.from_model_to_entity(result)