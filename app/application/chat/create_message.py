import uuid

from app.config.log_config import logger
from app.domain.interfaces.chat_gateway import ChatGateway
from app.domain.interfaces.member_room_association import MemberRoomAssociationGateway
from app.presentation.schemas.message_schemas import MessageCreate, MessageResponse
from app.domain.interfaces.room_gateway import RoomGateway

from app.domain.exceptions.exception import ServerError
from app.domain.exceptions.room_exception import RoomNotFoundError,UserNotInRoomError


class ChatService:

    def __init__(self,chat_repo: ChatGateway,room_repo: RoomGateway,member_room: MemberRoomAssociationGateway):
        self.chat_repo = chat_repo
        self.room_repo = room_repo
        self.member_room = member_room
        
    def create_message(self,room_id: uuid.UUID,user_id: uuid.UUID,message: MessageCreate) -> MessageResponse | list:
        """
        Создает новое сообщение в комнате.
        """
        room = self.room_repo.get_room_by_id(room_id)
        if not room:
            raise RoomNotFoundError()
        
        members = self.member_room.get_members_by_room_id(room_id)
        if not members:
            return []

        if user_id not in [member.user_id for member in members]:
            raise UserNotInRoomError()
        try:
            new_message = self.chat_repo.create_message(room_id,user_id,message.text)
        except Exception as e:
            logger.error(f'ChatService: произошла ошибка при отправке сообщения от пользователя {user_id} в комнату {room_id}.{e}',exc_info=True)
            raise ServerError(
                detail=f"Ошибка при создании сообщения: {e}"
            )
            
        return new_message

