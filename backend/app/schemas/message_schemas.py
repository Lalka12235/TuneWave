from pydantic import BaseModel, Field, ConfigDict
import uuid
from datetime import datetime


class MessageResponse(BaseModel):
    id: uuid.UUID
    text: str
    user_id: uuid.UUID
    room_id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MessageCreate(BaseModel):
    text: str = Field(..., max_length=1000)

