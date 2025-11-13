from pydantic import BaseModel,Field,ConfigDict
import uuid
from datetime import datetime
from app.domain.enum import FriendshipStatus
from app.presentation.schemas.user_schemas import UserResponse


class FriendshipRequestCreate(BaseModel):
    """
    Схема для отправки нового запроса на дружбу.
    Содержит ID пользователя, которому отправляется запрос.
    """
    accepter_id: uuid.UUID = Field(..., description="ID пользователя, которому отправляется запрос на дружбу.")


class FriendshipUpdateStatus(BaseModel):
    """
    Схема для обновления статуса запроса на дружбу (принять или отклонить).
    """
    status: FriendshipStatus = Field(..., description="Новый статус запроса: 'accepted' или 'declined'.")


class FriendshipResponse(BaseModel):
    """
    Схема для представления информации о запросе на дружбу или о статусе дружбы.
    """
    id: uuid.UUID = Field(..., description="Уникальный ID записи о дружбе.")
    requester_id: uuid.UUID = Field(..., description="ID пользователя, который отправил запрос.")
    accepter_id: uuid.UUID = Field(..., description="ID пользователя, который получил запрос.")
    status: FriendshipStatus = Field(..., description="Текущий статус дружбы: 'pending', 'accepted', 'declined'.")
    created_at: datetime = Field(..., description="Дата и время отправки запроса.")
    
    accepted_at: datetime | None = Field(None, description="Дата и время принятия запроса (будет null, если не принят).")

    requester: UserResponse = Field(..., description="Информация о пользователе, который отправил запрос.")
    accepter: UserResponse = Field(..., description="Информация о пользователе, который получил/принял запрос.")

    model_config = ConfigDict(from_attributes=True) 