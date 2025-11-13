from pydantic import BaseModel, Field,ConfigDict
import uuid
from datetime import datetime
from app.presentation.schemas.user_schemas import UserResponse

class JoinRoomRequest(BaseModel):
    """
    Схема для тела запроса при присоединении к комнате.
    Пароль опционален, так как публичные комнаты не требуют пароля.
    """
    password: str | None = Field(None, description="Пароль для приватной комнаты")


class RoomMemberResponse(BaseModel):
    user_id: uuid.UUID = Field(...,description='Уникальный ID пользователя')
    room_id: uuid.UUID = Field(...,description='Уникальный ID комнаты')
    joined_at: datetime = Field(...,description='Дата и время присоединения пользователя к комнате')
    role: str = Field(...,description='Роль пользователя в комнате (например, "member", "owner", "moderator")')
    user: UserResponse | None = Field(None,description='Полная информация о профиле пользователя, если загружена')

    model_config = ConfigDict(from_attributes=True)


class RoomMemberRoleUpdate(BaseModel):
    """
    Схема для тела запроса при изменении роли члена комнаты.
    """
    role: str = Field(..., description="Новая роль для члена комнаты (например, 'member', 'moderator')")
