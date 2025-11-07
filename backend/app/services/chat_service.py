import uuid
from datetime import datetime

from app.logger.log_config import logger
from app.repositories.abc.chat_repo import ABCChatRepository
from app.schemas.message_schemas import MessageCreate, MessageResponse
from app.repositories.abc.room_repo import ABCRoomRepository
from app.services.mappers.message_mapper import MessageMapper

from app.exceptions.exception import ServerError
from app.exceptions.room_exception import RoomNotFoundError,UserNotInRoomError


class ChatService:
    """
    Реализует бизнес логику для работы с чатом комнаты
    """

    def __init__(self,chat_repo: ABCChatRepository,room_repo: ABCRoomRepository,message_mapper: MessageMapper):
        self.chat_repo = chat_repo
        self.room_repo = room_repo
        self.message_mapper = message_mapper

    
    def get_message_for_room(self,room_id: uuid.UUID,limit:int = 50,before_timestamp: datetime | None = None) -> list[MessageResponse]:
        """
        Получает историю сообщений для указанной комнаты.

        Args:
            db (Session): Сессия базы данных.
            room_id (uuid.UUID): Уникальный идентификатор комнаты.
            limit (int, optional): Максимальное количество сообщений для возврата. По умолчанию 50.

        Raises:
            HTTPException: Если комната с указанным ID не найдена.

        Returns:
            list[MessageResponse]: Список объектов Pydantic, представляющих сообщения.
        """
        room = self.room_repo.get_room_by_id(room_id)
        if not room:
            raise RoomNotFoundError()
        
        if before_timestamp:
            messages = self.chat_repo.get_message_for_room(room_id,limit,before_timestamp)

        messages = self.chat_repo.get_message_for_room(room_id,limit)

        return [self.message_mapper.to_response(message) for message in messages]
    

    
    def create_message(self,room_id: uuid.UUID,user_id: uuid.UUID,message: MessageCreate) -> MessageResponse:
        """
        Создает новое сообщение в комнате.

        Args:
            db (Session): Сессия базы данных.
            room_id (uuid.UUID): Уникальный идентификатор комнаты.
            user_id (uuid.UUID): ID пользователя, который отправляет сообщение.
            message (MessageCreate): Pydantic-схема с текстом сообщения.

        Raises:
            HTTPException: Если комната не найдена или пользователь не является её участником.

        Returns:
            MessageResponse: Pydantic-схема созданного сообщения.
        """
        room = self.room_repo.get_room_by_id(room_id)
        if not room:
            raise RoomNotFoundError()
        
        members = room.member_room
        if not members:
            return []

        if user_id not in [member.id for member in members]:
            raise UserNotInRoomError()
        try:
            new_message = self.chat_repo.create_message(room_id,user_id,message.text)
        except Exception as e:
            logger.error(f'ChatService: произошла ошибка при отправке сообщения от пользователя {user_id} в комнату {room_id}.{e}',exc_info=True)
            raise ServerError(
                detail=f"Ошибка при создании сообщения: {e}"
            )
            
        return self.message_mapper.to_response(new_message)
    