from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Any

class SpotifyImage(BaseModel):
    """Схема для объекта изображения Spotify (например, обложки альбома или плейлиста)."""
    url: str = Field(..., description="URL изображения.")
    height: int | None = Field(None, description="Высота изображения в пикселях.")
    width: int | None  = Field(None, description="Ширина изображения в пикселях.")

    model_config = ConfigDict(from_attributes=True)


class SpotifyArtist(BaseModel):
    """Схема для объекта артиста Spotify."""
    id: str = Field(..., description="Уникальный Spotify ID артиста.")
    name: str = Field(..., description="Имя артиста.")
    uri: str = Field(..., description="Spotify URI артиста (например, 'spotify:artist:123xyz').")
    external_urls: dict[str, str] = Field(..., description="Словарь внешних URL, например, ссылка на Spotify.")

    model_config = ConfigDict(from_attributes=True)


class SpotifyAlbum(BaseModel):
    """Схема для объекта альбома Spotify."""
    id: str = Field(..., description="Уникальный Spotify ID альбома.")
    name: str = Field(..., description="Название альбома.")
    images: list[SpotifyImage] = Field(..., description="Список изображений обложки альбома.")
    uri: str = Field(..., description="Spotify URI альбома (например, 'spotify:album:123xyz').")

    model_config = ConfigDict(from_attributes=True)


class SpotifyTrackDetails(BaseModel):
    """Схема для детальной информации о треке Spotify."""
    id: str = Field(..., description="Уникальный Spotify ID трека.")
    name: str = Field(..., description="Название трека.")
    artists: list[SpotifyArtist] = Field(..., description="Список артистов трека.")
    album: SpotifyAlbum = Field(..., description="Объект альбома, к которому относится трек.")
    duration_ms: int = Field(..., description="Длительность трека в миллисекундах.")
    uri: str = Field(..., description="Spotify URI трека (например, 'spotify:track:123xyz').")
    is_playable: bool | None  = Field(None, description="Доступен ли трек для воспроизведения в текущем регионе.")
    preview_url: str | None  = Field(None, description="URL для 30-секундного аудио-превью трека.")

    model_config = ConfigDict(from_attributes=True)


class SpotifyPlaylistOwner(BaseModel):
    """Схема для объекта владельца плейлиста Spotify."""
    id: str = Field(..., description="Уникальный Spotify ID владельца.")
    display_name: str | None = Field(None, description="Отображаемое имя владельца плейлиста.")
    uri: str = Field(..., description="Spotify URI владельца.")
    external_urls: dict[str,str] | None = Field(None, description="Словарь внешних URL владельца.")

    model_config = ConfigDict(from_attributes=True)


class SpotifyPlaylistTrackItem(BaseModel):
    """Схема для элемента списка треков внутри плейлиста (содержит сам трек и метаданные)."""
    track: SpotifyTrackDetails | None  = Field(None, description="Детали трека. Может быть None, если трек недоступен.")
    added_at: datetime | None = Field(None, description="Дата и время добавления трека в плейлист.")
    added_by: Any | None = Field(None, description="Информация о пользователе, который добавил трек. Может быть сложным объектом или None.")

    model_config = ConfigDict(from_attributes=True)


class SpotifyPlaylistTracksPaging(BaseModel):
    """Схема для постраничного ответа со списком треков плейлиста."""
    href: str = Field(..., description="URL для текущего запроса.")
    limit: int = Field(..., description="Максимальное количество элементов в ответе.")
    next: str | None = Field(None, description="URL для следующей страницы (если есть).")
    offset: int = Field(..., description="Смещение текущей страницы.")
    previous: str | None = Field(None, description="URL для предыдущей страницы (если есть).")
    total: int = Field(..., description="Общее количество треков в плейлисте.")
    items: list[SpotifyPlaylistTrackItem] = Field(..., description="Список элементов треков.")

    model_config = ConfigDict(from_attributes=True)


class SpotifyPlaylistSearchItem(BaseModel):
    """Схема для объекта плейлиста, возвращаемого при поиске."""
    id: str = Field(..., description="Уникальный Spotify ID плейлиста.")
    name: str = Field(..., description="Название плейлиста.")
    description: str | None = Field(None, description="Описание плейлиста.")
    owner: SpotifyPlaylistOwner = Field(..., description="Информация о владельце плейлиста.")
    images: list[SpotifyImage] = Field(..., description="Список изображений обложки плейлиста.")
    tracks: SpotifyPlaylistTracksPaging = Field(..., description="Сводная информация о треках плейлиста (в поиске 'items' может быть пустым).")
    uri: str = Field(..., description="Spotify URI плейлиста (например, 'spotify:playlist:123xyz').")
    external_urls: dict[str, str] = Field(..., description="Словарь внешних URL, например, ссылка на Spotify.")

    model_config = ConfigDict(from_attributes=True)


class SpotifyPlaylistsSearchPaging(BaseModel):
    """Схема для объекта пагинации результатов поиска плейлистов."""
    href: str = Field(..., description="URL для текущего запроса.")
    limit: int = Field(..., description="Максимальное количество элементов в ответе.")
    next: str | None = Field(None, description="URL для следующей страницы (если есть).")
    offset: int = Field(..., description="Смещение текущей страницы.")
    previous: str | None = Field(None, description="URL для предыдущей страницы (если есть).")
    total: int = Field(..., description="Общее количество результатов поиска плейлистов.")
    items: list[SpotifyPlaylistSearchItem] = Field(..., description="Список найденных плейлистов.")
    model_config = ConfigDict(from_attributes=True)


class SpotifyPlaylistsSearchResponse(BaseModel):
    """Основная схема ответа для поиска плейлистов."""
    playlists: SpotifyPlaylistsSearchPaging = Field(..., description="Словарь, содержащий список найденных плейлистов.")

    model_config = ConfigDict(from_attributes=True)

