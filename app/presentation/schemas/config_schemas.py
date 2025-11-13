from pydantic import BaseModel, Field

class FrontendConfig(BaseModel):
    """
    Схема для передачи публичных конфигурационных данных на фронтенд.
    """
    google_client_id: str = Field(..., description="Client ID Google OAuth для фронтенда")
    google_redirect_uri: str = Field(..., description="Redirect URI Google OAuth для фронтенда")
    google_scopes: str = Field(..., description="Области доступа Google OAuth для фронтенда")

    spotify_client_id: str | None = Field(None, description="Client ID Spotify API для фронтенда")
    spotify_redirect_uri: str | None = Field(None, description="Redirect URI Spotify API для фронтенда")
    spotify_scopes: str | None = Field(None, description="Области доступа Spotify API для фронтенда")