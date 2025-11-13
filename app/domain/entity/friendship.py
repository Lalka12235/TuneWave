from dataclasses import dataclass
import uuid
from app.domain.enum import FriendshipStatus
from datetime import datetime

@dataclass(slots=True,frozen=True)
class FriendshipEntity:
    id: uuid.UUID
    requester_id: uuid.UUID
    accepter_id: uuid.UUID
    status: FriendshipStatus
    created_at: datetime
    accepted_at: datetime