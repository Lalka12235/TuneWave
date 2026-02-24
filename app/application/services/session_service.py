import secrets
from typing import NewType

SessionID = NewType('SessionID',str)

class SessionService:
    
    def generate_session_id(self) -> SessionID:
        secrets.token_hex(16)