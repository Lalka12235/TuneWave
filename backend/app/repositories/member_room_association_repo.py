from sqlalchemy import select,delete
from sqlalchemy.orm import Session
from app.models.member_room_association import Member_room_association
from app.models.user import User
from app.models.room import Room
import uuid


class MemberRoomAssociationRepository:
    """
    Репозиторий для выполнения операций CRUD над моделью Member_room_association.
    Отвечает за управление связями между пользователями и комнатами (членство).
    """

    @staticmethod
    def add_member(db: Session,user_id: uuid.UUID,room_id: uuid.UUID) -> Member_room_association:
        """
        Добавляет пользователя в комнату (создает запись о членстве).
        
        Args:
            db (Session): Сессия базы данных SQLAlchemy.
            user_id (uuid.UUID): ID пользователя, который присоединяется.
            room_id (uuid.UUID): ID комнаты, к которой присоединяется пользователь.
            
        Returns:
            Member_room_association: Созданный объект ассоциации.
        """
        new_member_room = Member_room_association(
            user_id=user_id,
            room_id=room_id,
        )
        db.add(new_member_room)
        return new_member_room
    

    @staticmethod
    def remove_member(db: Session,user_id: uuid.UUID, room_id: uuid.UUID) -> bool:
        """
        Удаляет пользователя из комнаты (удаляет запись о членстве).
        
        Args:
            db (Session): Сессия базы данных SQLAlchemy.
            user_id (uuid.UUID): ID пользователя, которого нужно удалить.
            room_id (uuid.UUID): ID комнаты, из которой нужно удалить пользователя.
            
        Returns:
            bool: True, если членство было успешно удалено, иначе False.
        """
        stmt = delete(Member_room_association).where(
            Member_room_association.room_id==room_id,
            Member_room_association.user_id==user_id,
        )
        result = db.execute(stmt)
        return result.rowcount > 0
    

    @staticmethod
    def get_association_by_ids(db: Session, user_id: uuid.UUID, room_id: uuid.UUID) -> Member_room_association | None:
        """
        Получает запись об ассоциации (членстве) по ID пользователя и ID комнаты.
        
        Args:
            db (Session): Сессия базы данных SQLAlchemy.
            user_id (uuid.UUID): ID пользователя.
            room_id (uuid.UUID): ID комнаты.
            
        Returns:
            Member_room_association | None: Объект ассоциации, если найден, иначе None.
        """

        stmt = select(Member_room_association).where(
            Member_room_association.room_id==room_id,
            Member_room_association.user_id==user_id,
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none()
    

    @staticmethod
    def get_members_by_room_id(db: Session, room_id: uuid.UUID) -> list[User]:
        """
        Получает список объектов User, которые являются участниками данной комнаты.
        
        Args:
            db (Session): Сессия базы данных SQLAlchemy.
            room_id (uuid.UUID): ID комнаты.
            
        Returns:
            List[User]: Список объектов User, являющихся участниками комнаты.
        """
        stmt = select(User).join(Member_room_association).where(
            Member_room_association.room_id == room_id
        )
        result = db.execute(stmt)
        return result.scalars().all()
    

    @staticmethod
    def get_rooms_by_user_id(db: Session, user_id: uuid.UUID) -> list[Room]:
        """
        Получает список объектов Room, в которых состоит данный пользователь.
        
        Args:
            db (Session): Сессия базы данных SQLAlchemy.
            user_id (uuid.UUID): ID пользователя.
            
        Returns:
            List[Room]: Список объектов Room, в которых состоит пользователь.
        """
        # ДОБАВЛЕНО: Этот метод аналогичен get_members_by_room_id, но выбирает Room.
        stmt = select(Room).join(Member_room_association).where(
            Member_room_association.user_id == user_id
        )
        result = db.execute(stmt)
        return result.scalars().all()