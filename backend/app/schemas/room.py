from pydantic import BaseModel, Field, ConfigDict 
from datetime import datetime
import uuid

class RoomBase(BaseModel):
    """
    Базовая схема для комнаты, содержит общие поля.
    """
    name: str = Field(..., min_length=3, max_length=50, description="Название комнаты (от 3 до 50 символов)")
    max_members: int = Field(..., gt=0, description="Максимальное количество участников (больше 0)")
    is_private: bool = Field(..., description="Приватная ли комната (True/False)")



class RoomCreate(RoomBase):
    """
    Схема для создания новой комнаты.
    Наследует поля из RoomBase.
    password_hash опционален и нужен только если is_private=True.
    """
    password: str | None = Field(None, min_length=6, max_length=100, description="Пароль для приватной комнаты (если is_private=True)")


class RoomUpdate(BaseModel):
    """
    Схема для обновления существующей комнаты.
    Все поля опциональны, так как можно обновлять только часть данных.
    """
    name: str | None = Field(None, min_length=3, max_length=50, description="Новое название комнаты")
    max_members: int | None = Field(None, gt=0, description="Новое максимальное количество участников")
    is_private: bool | None = Field(None, description="Изменить приватность комнаты")
    password: str | None = Field(None, min_length=6, max_length=100, description="Новый пароль для приватной комнаты")
    description: str | None = Field(None, max_length=255, description="Новое описание комнаты")


class RoomResponse(RoomBase):
    """
    Схема для возврата информации о комнате.
    Включает ID, время создания и ID владельца, а также поля из RoomBase.
    """
    id: uuid.UUID = Field(..., description="Уникальный идентификатор комнаты")
    owner_id: uuid.UUID = Field(..., description="ID пользователя-владельца комнаты")
    created_at: datetime = Field(..., description="Время создания комнаты")


    current_track_id: uuid.UUID | None = Field(None, description="ID текущего воспроизводимого трека")
    current_track_position_ms: int | None = Field(None, description="Позиция воспроизведения текущего трека в мс")
    is_playing: bool = Field(..., description="Воспроизводится ли музыка в данный момент")

    model_config = ConfigDict(from_attributes=True)