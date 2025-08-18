from pydantic import BaseModel, Field, ConfigDict
import uuid
from datetime import datetime


class TrackBase(BaseModel):
    """Базовая схема для информации о треке."""
    spotify_id: str = Field(..., description="Уникальный ID трека на Spotify.")
    spotify_uri: str = Field(..., description="Spotify URI трека (например, 'spotify:track:123xyz').")
    title: str = Field(..., description="Название трека.")
    artist_names: list[str] = Field(..., description="Список имен исполнителей трека.")
    album_name: str = Field(..., description="Название альбома, к которому относится трек.")
    album_cover_url: str | None = Field(None, description="URL обложки альбома.")
    duration_ms: int = Field(..., description="Длительность трека в миллисекундах.")
    is_playable: bool = Field(True, description="Доступен ли трек для воспроизведения.")
    spotify_track_url: str | None = Field(None, description="Ссылка на трек на Spotify.")

    model_config = ConfigDict(from_attributes=True)


class TrackCreate(TrackBase):
    """Схема для создания нового трека (обычно используется внутренне, когда кешируем трек из Spotify)."""
    pass


class TrackResponse(TrackBase):
    """Схема для ответа с детальной информацией о треке из вашей базы данных."""
    id: uuid.UUID = Field(..., description="Уникальный ID трека в вашей базе данных.")
    last_synced_at: datetime = Field(..., description="Время последней синхронизации метаданных трека с Spotify.") 
    created_at: datetime = Field(..., description="Время добавления записи трека в локальную базу данных.")