from sqlalchemy import select,delete
from sqlalchemy.orm import Session
from app.models.ban import Ban
import uuid


class BanRepository:
    """
    Репозиторий для выполнения операций CRUD над моделью Ban.
    Отвечает за управление записями о банах пользователей.
    """
    def __init__(self, db: Session):
        self.db: Session = db

    
    def get_bans_by_admin(self,user_id: uuid.UUID) -> list[Ban]:
        """
        Получает список банов, выданных указанным пользователем (кто забанил).

        Args:
            db (Session): Сессия базы данных SQLAlchemy.
            user_id (uuid.UUID): ID пользователя, который выдал бан.

        Returns:
            List[Ban]: Список объектов Ban, выданных этим пользователем.
        """
        stmt = select(Ban).where(
            Ban.by_ban_user_id== user_id,
        )
        result = self.db.execute(stmt)
        return result.scalars().all()
    

    
    def get_bans_on_user(self,user_id: uuid.UUID) -> list[Ban]:
        """
        Получает список банов, полученных указанным пользователем (кого забанили).

        Args:
            db (Session): Сессия базы данных SQLAlchemy.
            user_id (uuid.UUID): ID пользователя, который был забанен.

        Returns:
            List[Ban]: Список объектов Ban, полученных этим пользователем.
        """
        stmt = select(Ban).where(
            Ban.ban_user_id == user_id,
        )
        result = self.db.execute(stmt)
        return result.scalars().all()
    

    
    def add_ban(self,room_id: uuid.UUID,ban_user_id: uuid.UUID,reason: str,by_ban_user_id: uuid.UUID) -> Ban | None:
        """
        Добавляет новую запись о бане в базу данных.

        Args:
            db (Session): Сессия базы данных SQLAlchemy.
            ban_user_id (uuid.UUID): ID пользователя, которого нужно забанить.
            reason (Optional[str]): Причина бана.
            by_ban_user_id (uuid.UUID): ID пользователя, который выдал бан.
            room_id (Optional[uuid.UUID]): ID комнаты, в которой выдан бан. None для глобального бана.

        Returns:
            Ban: Созданный объект Ban.
        """
        new_ban_user = Ban(
            ban_user_id=ban_user_id,
            room_id=room_id,
            reason=reason,
            by_ban_user_id=by_ban_user_id,
        )
        self.db.add(new_ban_user)
        self.db.flush()
        return new_ban_user
    

    
    def remove_ban_local(self,room_id: uuid.UUID,ban_user_id: uuid.UUID) -> bool:
        """
        Удаляет запись о бане из базы данных.

        Args:
            db (Session): Сессия базы данных SQLAlchemy.
            ban_user_id (uuid.UUID): ID пользователя, с которого нужно снять бан.
            room_id (Optional[uuid.UUID]): ID комнаты, в которой нужно снять бан. None для глобального бана.

        Returns:
            bool: True, если бан был успешно удален, иначе False.
        """
        stmt = delete(Ban).where(
            Ban.room_id == room_id,
            Ban.ban_user_id == ban_user_id,
        )
        result = self.db.execute(stmt)
        return result.rowcount > 0
    

    
    def remove_ban_global(self,ban_user_id: uuid.UUID) -> bool:
        """_summary_

        Args:
            db (Session): _description_
            ban_user_id (uuid.UUID): _description_

        Returns:
            bool: _description_
        """
        stmt = delete(Ban).where(
                Ban.ban_user_id == ban_user_id,
                Ban.room_id.is_(None)
        )
        result = self.db.execute(stmt)
        return result.rowcount > 0
    


    
    def is_user_banned_global(self, user_id: uuid.UUID) -> Ban | None:
        """
        Проверяет, забанен ли пользователь ГЛОБАЛЬНО (то есть, во всех комнатах).

        Args:
            db (Session): Сессия базы данных SQLAlchemy.
            user_id (uuid.UUID): ID пользователя для проверки.

        Returns:
            Ban | None: Объект Ban, если пользователь забанен глобально, иначе None.
        """
        stmt = select(Ban).where(
                Ban.ban_user_id == user_id,
                Ban.room_id.is_(None)
        )
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    
    
    def is_user_banned_local(self, user_id: uuid.UUID,room_id: uuid.UUID) -> Ban | None:
        """
        Проверяет, забанен ли пользователь в КОНКРЕТНОЙ комнате.

        Args:
            db (Session): Сессия базы данных SQLAlchemy.
            user_id (uuid.UUID): ID пользователя для проверки.
            room_id (uuid.UUID): ID комнаты, для которой проверяется бан.

        Returns:
            Ban | None: Объект Ban, если пользователь забанен в указанной комнате, иначе None.
        """
        stmt = select(Ban).where(
                Ban.ban_user_id == user_id,
                Ban.room_id == room_id
        )
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()
