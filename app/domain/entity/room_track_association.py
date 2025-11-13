from dataclasses import dataclass
import uuid
from datetime import datetime


@dataclass(slots=True,frozen=True)
class RoomTrackAssociationEntity:
    """
    Сущность модели RoomTrackAssociation
    """
    id: uuid.UUID
    room_id: uuid.UUID
    track_id: uuid.UUID
    order_in_queue: int
    added_at: datetime
    added_by_user_id: uuid.UUID