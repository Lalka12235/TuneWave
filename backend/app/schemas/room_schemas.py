from pydantic import BaseModel, Field, ConfigDict
import uuid
from datetime import datetime
from app.schemas.user_schemas import UserResponse
from app.schemas.track_schemas import TrackResponse


class TrackInQueueResponse(BaseModel):
    track: TrackResponse = Field(..., description="Информация о треке")
    order_in_queue: int = Field(..., description="Позиция трека в очереди")
    association_id: uuid.UUID = Field(..., description="ID ассоциации трека с комнатой", alias="id")
    added_at: datetime = Field(...,description='Время создания трека в очереди')

    model_config = ConfigDict(from_attributes=True)


class AddTrackToQueueRequest(BaseModel):
    spotify_id: str = Field(..., description="Spotify ID трека для добавления в очередь")


class RemoveTrackFromQueueRequest(BaseModel):
    association_id: uuid.UUID = Field(..., description="ID ассоциации трека с комнатой для удаления")


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
    password опционален и нужен только если is_private=True.
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


class RoomResponse(RoomBase):
    """
    Схема для возврата информации о комнате.
    Включает ID, время создания и ID владельца, а также поля из RoomBase.
    """
    id: uuid.UUID = Field(..., description="Уникальный идентификатор комнаты")
    owner_id: uuid.UUID = Field(..., description="ID пользователя-владельца комнаты")
    created_at: datetime = Field(..., description="Время создания комнаты")
    #updated_at: datetime | None = Field(None, description="Время последнего обновления комнаты")
    current_track_id: uuid.UUID | None = Field(None, description="ID текущего воспроизводимого трека")
    current_track_position_ms: int | None = Field(None, description="Позиция воспроизведения текущего трека в мс")
    is_playing: bool = Field(..., description="Воспроизводится ли музыка в данный момент")
    current_members_count: int = Field(..., description="Текущее количество участников в комнате")
    queue: list[TrackInQueueResponse] = Field([], description="Очередь треков в комнате")
    owner: UserResponse | None = Field(None, description="Информация о владельце комнаты")
    members: list[UserResponse] = Field([], description="Список участников комнаты")

    model_config = ConfigDict(from_attributes=True)


class RoomJoinRequest(BaseModel):
    password: str | None = Field(None, description="Пароль для приватной комнаты")


class RoomMemberResponse(BaseModel):
    id: uuid.UUID
    username: str
    
    model_config = ConfigDict(from_attributes=True)


class InviteResponse(BaseModel):
    action: str = Field(..., description='Действие: "accept" для принятия, "decline" для отклонения.')