from pydantic import BaseModel, ConfigDict
import uuid
from datetime import datetime
from app.presentation.schemas.track_schemas import TrackResponse

class FavoriteTrackResponse(BaseModel):
    user_id: uuid.UUID
    track_id: uuid.UUID
    added_at: datetime
    track: TrackResponse

    model_config = ConfigDict(from_attributes=True)


class FavoriteTrackAdd(BaseModel):
    spotify_id: str