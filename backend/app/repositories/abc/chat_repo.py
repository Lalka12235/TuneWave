from abc import ABC,abstractmethod
import uuid
from app.schemas.entity import MessageEntity
from datetime import datetime


class ChatRepository(ABC):
    """
    Абстрактный репозиторий для работы с чатом комнаты.
    """

    @abstractmethod
    def get_message_for_room(self,room_id: uuid.UUID,limit: int = 50,before_timestamp: datetime | None = None) -> list[MessageEntity]:
        """
        Возвращает все сообщения в комнате
        """
    
    @abstractmethod
    def create_message(self,room_id: uuid.UUID,user_id: uuid.UUID,text: str) -> MessageEntity:
        """
        Создает сообщение в базе данных
        """