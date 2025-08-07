from fastapi import HTTPException,status
from sqlalchemy.orm import Session
from app.repositories.chat_repo import ChatRepository
from app.schemas.message_schemas import MessageCreate,MessageResponse
from app.services.room_service import RoomService
from app.models.message import Message
import uuid
from datetime import datetime



class ChatService():

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


    @staticmethod
    def get_message_for_room(db: Session,room_id: uuid.UUID,limit:int = 50,before_timestamp: datetime | None = None) -> list[MessageResponse]:
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
        RoomService.get_room_by_id(db,room_id)
        
        if before_timestamp:
            messages = ChatRepository.get_message_for_room(db,room_id,limit,before_timestamp)

        messages = ChatRepository.get_message_for_room(db,room_id,limit)

        return [ChatService._map_message_to_response(message) for message in messages]
    

    @staticmethod
    def create_message(db: Session,room_id: uuid.UUID,user_id: uuid.UUID,message: MessageCreate) -> MessageResponse:
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
        RoomService.get_room_by_id(db,room_id)

        user_in_room = RoomService.get_room_members(db,room_id)

        if user_id not in [member.id for member in user_in_room]:
            raise HTTPException(
                status_code=403,
                detail='Вы не находитесь в комнате'
            )
        try:
            new_message = ChatRepository.create_message(db,room_id,user_id,message.text)
            db.commit()
            db.refresh(new_message)
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Ошибка при создании сообщения: {e}"
            )
            
        

        return ChatService._map_message_to_response(new_message)
    