from pydantic import BaseModel, Field, ConfigDict
import uuid


class TrackBase(BaseModel):
    spotify_track_id: str = Field(..., description="ID трека на Spotify")
    title: str = Field(..., description="Название трека")
    artist: str = Field(..., description="Исполнитель трека")
    album: str = Field(..., description="Название альбома")
    image_url: str | None = Field(None, description="URL обложки альбома")
    duration_ms: int = Field(..., description="Длительность трека в миллисекундах")
    spotify_track_url: str | None = Field(None, description="Ссылка на трек на Spotify")
    spotify_uri: str = Field(...,description='')

class TrackCreate(TrackBase):
    pass

class TrackResponse(TrackBase):
    id: uuid.UUID = Field(..., description="Уникальный ID трека в вашей базе данных")
    #updated_at: str | None = Field(None, description="Дата и время последнего обновления записи")

    model_config = ConfigDict(from_attributes=True)