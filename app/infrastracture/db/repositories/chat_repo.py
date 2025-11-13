from sqlalchemy import select
from sqlalchemy.orm import Session,joinedload
from app.infrastracture.db.models import Message
from datetime import datetime
import uuid
from app.domain.interfaces.chat_repo import ChatRepository
from app.domain.entity import MessageEntity


class SQLalchemyChatRepository(ChatRepository):

    def __init__(self, db: Session):
        self._db: Session = db

    
    def from_model_to_entity(self,model: Message) -> MessageEntity | None:
        return MessageEntity(
            id=model.id,
            text=model.text,
            user_id=model.user_id,
            room_id=model.room_id,
            created_at=model.created_at,
        )

    def get_message_for_room(self,room_id: uuid.UUID,limit: int = 50,before_timestamp: datetime | None = None) -> list[MessageEntity]:
        """Возвращает все сообщения в комнате

        Args:
            room_id (uuid.UUID): Для нахождения сообщений в нужной комнате

        Returns:
            list[Message]: Возвращает список найденных сообщений
        """
        stmt = (
            select(Message)
            .where(Message.room_id == room_id)
            .order_by((Message.created_at).desc())
            .limit(limit)
            .options(joinedload(Message.user))
        )

        if before_timestamp:
            stmt = stmt.where(Message.created_at < before_timestamp)

        result = self._db.execute(stmt)
        result = result.scalars().all()
        return result
    

    
    def create_message(self,room_id: uuid.UUID,user_id: uuid.UUID,text: str) -> MessageEntity:
        """Создает сообщение в базе данных

        Args:
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
        self._db.add(new_message)
        self._db.flush()
        return self.from_model_to_entity(new_message)