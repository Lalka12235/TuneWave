import uuid
from datetime import datetime

from app.domain.entity.message import MessageEntity
from app.domain.interfaces.chat_gateway import ChatGateway
from app.domain.interfaces.room_gateway import RoomGateway

from app.domain.exceptions.room_exception import RoomNotFoundError


class ReadMessage:

    def __init__(self,chat_repo: ChatGateway,room_repo: RoomGateway):
        self.chat_repo = chat_repo
        self.room_repo = room_repo

    
    def get_message_for_room(self,room_id: uuid.UUID,limit:int = 50,before_timestamp: datetime | None = None) -> list[MessageEntity]:
        """
        Получает историю сообщений для указанной комнаты.
        """
        room = self.room_repo.get_room_by_id(room_id)
        if not room:
            raise RoomNotFoundError()
        
        if before_timestamp:
            messages = self.chat_repo.get_message_for_room(room_id,limit,before_timestamp)

        messages = self.chat_repo.get_message_for_room(room_id,limit)

        return [message for message in messages]