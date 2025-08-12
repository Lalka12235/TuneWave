from pydantic import BaseModel, Field, ConfigDict
import uuid
from app.schemas.user_schemas import UserResponse 
from app.schemas.room_schemas import RoomResponse
from datetime import datetime



class BanCreate(BaseModel):
    """
    Схема для создания новой записи о бане.
    """
    ban_user_id: uuid.UUID = Field(..., description="ID пользователя, которого нужно забанить.")
    room_id: uuid.UUID | None = Field(None, description="ID комнаты, в которой выдан бан. Оставьте None для глобального бана.")
    reason: str | None  = Field(None, description="Причина бана (необязательно).")


class BanRemove(BaseModel):
    """
    Схема для создания новой записи о бане.
    """
    ban_user_id: uuid.UUID = Field(..., description="ID пользователя, которого нужно забанить.")
    room_id: uuid.UUID | None = Field(None, description="ID комнаты, в которой выдан бан. Оставьте None для глобального бана.")





class BanResponse(BaseModel):
    """
    Схема для представления информации о бане.
    """
    id: uuid.UUID = Field(..., description="Уникальный ID записи о бане.")
    ban_user_id: uuid.UUID = Field(..., description="ID пользователя, который был забанен.")
    room_id: uuid.UUID | None  = Field(None, description="ID комнаты, в которой выдан бан (None для глобального бана).")
    reason: str | None  = Field(None, description="Причина бана.")
    ban_date: datetime = Field(..., description="Дата и время выдачи бана.")
    by_ban_user_id: uuid.UUID = Field(..., description="ID пользователя, который выдал бан.")


    #banned_user: UserResponse | None = Field(None, description="Информация о забаненном пользователе.")
    #banned_by_user: UserResponse | None = Field(None, description="Информация о пользователе, который выдал бан.")
    #room: RoomResponse | None = Field(None, description="Информация о комнате, если бан привязан к комнате.")

    model_config = ConfigDict(from_attributes=True)