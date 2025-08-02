from app.models.room import Room
from sqlalchemy import select,delete
from sqlalchemy.orm import Session,joinedload
import uuid
from typing import Any
from app.models.member_room_association import Member_room_association
from app.models.room_track_association import RoomTrackAssociationModel
from app.models.user import User


class RoomRepository:
    """
    Репозиторий для выполнения операций CRUD (Create, Read, Update, Delete)
    над моделью Room в базе данных.
    """

    @staticmethod
    def get_room_by_id(db: Session, room_id: uuid.UUID) -> Room | None:
        """
        Получает комнату по ее уникальному идентификатору (ID).

        Args:
            db (Session): Сессия базы данных SQLAlchemy.
            room_id (uuid.UUID): ID комнаты для поиска.

        Returns:
            Room | None: Объект комнаты, если найден, иначе None.
        """
        stmt = select(Room).options(
            joinedload(Room.user), # Загружаем владельца
            joinedload(Room.member_room).joinedload(Member_room_association.user), # Загружаем участников и их пользователей
            joinedload(Room.room_track).joinedload(RoomTrackAssociationModel.track) # Загружаем очередь и связанные треки
        ).filter(Room.id == room_id)
        result = db.execute(stmt)
        # КРИТИЧНО: .unique() для joinedload с коллекциями
        return result.unique().scalar_one_or_none()
    
    @staticmethod
    def get_room_by_name(db: Session, name: str) -> Room | None:
        """
        Получает комнату по ее названию.

        Args:
            db (Session): Сессия базы данных SQLAlchemy.
            name (str): Название комнаты для поиска.

        Returns:
            Room | None: Объект комнаты, если найден, иначе None.
        """
        stmt = select(Room).options(
            joinedload(Room.user),
            joinedload(Room.member_room).joinedload(Member_room_association.user),
            joinedload(Room.room_track).joinedload(RoomTrackAssociationModel.track)
        ).filter(Room.name == name)
        result = db.execute(stmt)
        return result.unique().scalar_one_or_none()

    @staticmethod
    def get_all_rooms(db: Session) -> list[Room]:
        """
        Получает список всех комнат из базы данных.

        Args:
            db (Session): Сессия базы данных SQLAlchemy.

        Returns:
            List[Room]: Список объектов Room.
        """
        stmt = select(Room).options(
            joinedload(Room.user),
            joinedload(Room.member_room).joinedload(Member_room_association.user),
            joinedload(Room.room_track).joinedload(RoomTrackAssociationModel.track)
        )
        result = db.execute(stmt)
        return result.unique().scalars().all()
    


    @staticmethod
    def create_room(db: Session,room_data: dict[str, Any]) -> Room:
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
        db.add(new_room)
        return new_room
    
    @staticmethod
    def update_room(db: Session,room: Room, update_data: dict[str,Any]) -> Room:
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
        return room


    @staticmethod
    def delete_room(db: Session, room_id: uuid.UUID) -> bool:
        """
        Удаляет комнату из базы данных по ее ID.

        Args:
            db (Session): Сессия базы данных SQLAlchemy.
            room_id (uuid.UUID): ID комнаты для удаления.

        Returns:
            bool: True, если комната была успешно удалена, иначе False.
        """
        stmt = delete(Room).where(Room.id == room_id)
        result = db.execute(stmt)
        return result.rowcount > 0
    

    @staticmethod
    def get_active_rooms(db: Session) -> list[Room]:
        """
        Возвращает список комнат, в которых сейчас играет музыка.
        Связанные объекты current_track загружаются одним запросом.
        """
        stmt = select(Room).where(
            Room.is_playing == True,
        ).options(
            joinedload(Room.room_track),
        )
        result = db.execute(stmt)
        return result.scalars().all()
    

    @staticmethod
    def get_owner_room(db: Session,room_id: uuid.UUID) -> User | None:
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
            joinedload(Room.user),
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none()
    
