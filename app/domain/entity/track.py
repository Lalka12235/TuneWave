from dataclasses import dataclass
import uuid
from datetime import datetime

@dataclass(slots=True,frozen=True)
class TrackEntity:
    """
    Сущность модели Track
    """
    id: uuid.UUID
    spotify_id: str
    spotify_uri: str
    title: str
    artist_names: list[str]
    album_name: str
    album_cover_url: str | None
    duration_ms: int
    is_playable: bool
    spotify_track_url: str | None
    last_synced_at: datetime
    created_at: datetime