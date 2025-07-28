from pydantic import BaseModel, Field

class JoinRoomRequest(BaseModel):
    """
    Схема для тела запроса при присоединении к комнате.
    Пароль опционален, так как публичные комнаты не требуют пароля.
    """
    password: str | None = Field(None, description="Пароль для приватной комнаты")