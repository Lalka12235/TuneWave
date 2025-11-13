from dataclasses import dataclass
import uuid
from app.domain.enum.enum import FriendshipStatus
from datetime import datetime

@dataclass
class FriendshipEntity:
    id: uuid.UUID
    requester_id: uuid.UUID
    accepter_id: uuid.UUID
    status: FriendshipStatus
    created_at: datetime
    accepted_at: datetime