from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASS: str
    DB_NAME: str

    #GOOGLE_CLIENT_ID: str = Field(..., env="GOOGLE_CLIENT_ID")
    #GOOGLE_CLIENT_SECRET: str = Field(..., env="GOOGLE_CLIENT_SECRET")
    ## URI перенаправления, который вы зарегистрировали в Google Cloud Console
    #GOOGLE_REDIRECT_URI: str = Field(..., env="GOOGLE_REDIRECT_URI")
    ## Области доступа (scopes), которые вы запрашиваете у пользователя Google
    #GOOGLE_SCOPES: str = "openid email profile" # Базовые скоупы для получения email и профиля
#
    ## --- Настройки Spotify API (для доступа к музыке) ---
    ## Client ID вашего приложения Spotify
    #SPOTIFY_CLIENT_ID: str = Field(..., env="SPOTIFY_CLIENT_ID")
    ## Client Secret вашего приложения Spotify
    #SPOTIFY_CLIENT_SECRET: str = Field(..., env="SPOTIFY_CLIENT_SECRET")
    ## URI перенаправления, который вы зарегистрировали в приложении Spotify
    ## Может отличаться от Google Redirect URI, так как это для другого OAuth потока.
    #SPOTIFY_REDIRECT_URI: str = Field(..., env="SPOTIFY_REDIRECT_URI")
    ## Области доступа (scopes), которые вы запрашиваете у пользователя Spotify
    ## Эти скоупы позволят вашему приложению управлять воспроизведением и читать данные пользователя.
    #SPOTIFY_SCOPES: str = (
    #    "user-read-private user-read-email "
    #    "user-top-read user-read-playback-state user-modify-playback-state "
    #    "playlist-read-private playlist-read-collaborative user-library-read "
    #    "streaming app-remote-control user-read-currently-playing"
    #)

    @property
    def sync_db_url(self):
        return f'postgresql+psycopg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}'
    
    @property
    def async_db_url(self):
        return f'postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}'
    
    class Config:
        env_file = '.env'




settings = Settings()