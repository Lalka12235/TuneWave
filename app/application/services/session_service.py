import uuid
from typing import NewType

SessionID = NewType('SessionID',uuid.UUID)

class SessionService:
    
    def generate_session_id(self) -> SessionID:
        return SessionID(uuid.uuid4())
