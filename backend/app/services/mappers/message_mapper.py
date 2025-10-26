from app.models import Message
from app.schemas.message_schemas import MessageResponse
from app.services.mappers.base_mapper import BaseMapper
from app.services.mappers.user_mapper import UserMapper

class MessageMapper(BaseMapper):
    def __init__(self, user_mapper: UserMapper):
        self._user_mapper = user_mapper

    def to_response(self, message: Message) -> MessageResponse:
        return MessageResponse(
            id=message.id,
            content=message.content,
            sender=self._user_mapper.to_response(message.sender),
            room_id=message.room_id,
            created_at=message.created_at
        )