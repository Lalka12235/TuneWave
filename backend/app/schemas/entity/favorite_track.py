from dataclasses import dataclass
import uuid
from datetime import datetime

@dataclass
class FavoriteTrackEntity:
    user_id: uuid.UUID
    track_id: uuid.UUID
    added_at: datetime