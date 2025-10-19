import uuid
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.logger.log_config import logger
from app.models.message import Message
from app.repositories.chat_repo import ChatRepository
from app.schemas.message_schemas import MessageCreate, MessageResponse
from app.services.room_service import RoomService


class ChatService():

    def __init__(self,db: Session,chat_repo: ChatRepository,room_service: RoomService):
        self._db = db
        self.chat_repo = chat_repo
        self.room_service = room_service

    @staticmethod
    def _map_message_to_response(message: Message) -> MessageResponse:
        """
        Преобразует объект модели Message в Pydantic-схему MessageResponse.

        Args:
            message (Message): Объект сообщения из базы данных.

        Returns:
            MessageResponse: Pydantic-схема, готовая к отправке клиенту.
        """
        return MessageResponse.model_validate(message)


    
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
        self.room_service.get_room_by_id(room_id)
        
        if before_timestamp:
            messages = self.chat_repo.get_message_for_room(room_id,limit,before_timestamp)

        messages = self.chat_repo.get_message_for_room(room_id,limit)

        return [self._map_message_to_response(message) for message in messages]
    

    
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
        self.room_service.get_room_by_id(room_id)

        user_in_room = self.room_service.get_room_members(room_id)

        if user_id not in [member.id for member in user_in_room]:
            raise HTTPException(
                status_code=403,
                detail='Вы не находитесь в комнате'
            )
        try:
            new_message = self.chat_repo.create_message(room_id,user_id,message.text)
            self._db.commit()
            self._db.refresh(new_message)
        except Exception as e:
            logger.error(f'ChatService: произошла ошибка при отправке сообщения от пользователя {user_id} в комнату {room_id}.{e}',exc_info=True)
            self._db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Ошибка при создании сообщения: {e}"
            )
            
        

        return self._map_message_to_response(new_message)
    