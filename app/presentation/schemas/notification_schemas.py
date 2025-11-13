from pydantic import BaseModel,Field,ConfigDict
import uuid
from app.domain.enum.enum import NotificationType
from app.presentation.schemas.user_schemas import UserResponse
from datetime import datetime


class NotificationResponse(BaseModel):
    """
    Схема для представления информации об уведомлении.
    """
    id: uuid.UUID = Field(..., description="Уникальный ID уведомления.")
    user_id: uuid.UUID = Field(..., description="ID пользователя, который получает уведомление.")
    
    sender: UserResponse | None = Field(None, description="Информация об отправителе уведомления (если есть).")
    
    room_id: uuid.UUID | None = Field(None, description="ID комнаты, к которой относится уведомление (если есть).")

    notification_type: NotificationType = Field(..., description="Тип уведомления.")
    message: str = Field(..., description="Основной текст уведомления.")
    
    is_read: bool = Field(..., description="Статус прочитанности уведомления.")
    
    created_at: datetime = Field(..., description="Дата и время создания уведомления.")

    model_config = ConfigDict(from_attributes=True)
