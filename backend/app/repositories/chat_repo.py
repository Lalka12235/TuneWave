from sqlalchemy import select,delete
from sqlalchemy.orm import Session,joinedload
from app.models.message import Message
from app.models.room import Room
from datetime import datetime
import uuid


class ChatRepository:

    @staticmethod
    def get_message_for_room(db: Session,room_id: uuid.UUID,limit: int = 50,before_timestamp: datetime | None = None) -> list[Message]:
        """Возвращает все сообщения в комнате

        Args:
            db (Session): Сессия базы данных
            room_id (uuid.UUID): Для нахождения сообщений в нужной комнате

        Returns:
            list[Message]: Возвращает список найденных сообщений
        """
        stmt = select(Message).where(
            Message.created_at < before_timestamp
        ).filter(
            Message.room_id == room_id
        ).order_by(
            Message.created_at.asc()
        ).limit(limit).options(
            joinedload(Message.user)
        )
        return db.execute(stmt).scalars().all()

    

    @staticmethod
    def create_message(db: Session,room_id: uuid.UUID,user_id: uuid.UUID,text: str) -> Message:
        """Создает сообщение в базе данных

        Args:
            db (Session): Сессия базы данных
            room_id (uuid.UUID): Комната в которой создается сообщение
            user_id (uuid.UUID): Кто отправляет сообщение
            text (str): Сообщение создаваемое в базе данных

        Returns:
            Message: Возвращает данные сообщения
        """
        new_message = Message(
            room_id=room_id,
            user_id=user_id,
            text=text,
        )
        db.add(new_message)
        db.commit()
        db.refresh(new_message)
        return new_message