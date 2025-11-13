from dataclasses import dataclass
import uuid
from datetime import datetime


@dataclass(slots=True,frozen=True)
class RoomEntity:
    """
    Сущность модели Room
    """
    id: uuid.UUID
    name: str
    max_members: int
    owner_id: uuid.UUID
    is_private: bool
    password_hash: str
    current_track_id: uuid.UUID | None
    current_track_position_ms: int | None
    is_playing: bool
    created_at: datetime
    playback_host_id: uuid.UUID | None
    active_spotify_device_id: str | None
    current_playing_track_association_id: uuid.UUID | None