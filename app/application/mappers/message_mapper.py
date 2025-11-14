from app.domain.entity import MessageEntity
from app.presentation.schemas.message_schemas import MessageResponse
from app.application.mappers.user_mapper import UserMapper

class MessageMapper:
    def __init__(self, user_mapper: UserMapper):
        self._user_mapper = user_mapper

    def to_response(self, message: MessageEntity) -> MessageResponse:
        return MessageResponse(

        )