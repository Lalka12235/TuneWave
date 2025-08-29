from pydantic_settings import BaseSettings, SettingsConfigDict 
from pydantic import Field 
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    """
    Класс настроек приложения, загружающий переменные из окружения.
    Использует Pydantic-Settings для безопасной и удобной работы с конфигурацией.
    """
    BASE_URL: str = 'http://127.0.0.1:8000'

    APP_CONFIG_DB_URL: str = Field(..., env="APP_CONFIG_DB_URL", description="Полный URL для подключения к базе данных")
    # --- Настройки базы данных ---
    DB_HOST: str = Field(..., description="Хост базы данных PostgreSQL")
    DB_PORT: int = Field(..., description="Порт базы данных PostgreSQL")
    DB_USER: str = Field(..., description="Имя пользователя базы данных PostgreSQL")
    DB_PASS: str = Field(..., description="Пароль пользователя базы данных PostgreSQL")
    DB_NAME: str = Field(..., description="Имя базы данных PostgreSQL")

    JWT_SECRET_KEY: str = Field(..., env="JWT_SECRET_KEY", description="Секретный ключ для подписи JWT-токенов")
    ALGORITHM: str = Field("HS256", description="Алгоритм шифрования для JWT")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(15, description="Время жизни токена доступа JWT в минутах")

    # --- Настройки Профиля ---
    MAX_AVATAR_SIZE_BYTES: int = 5 * 1024 * 1024 
    BACKEND_ROOT: Path = Path(__file__).resolve().parent.parent.parent
    AVATARS_STORAGE_DIR: Path = BACKEND_ROOT / "avatars"



    # --- Настройки Google OAuth2 ---
    # GOOGLE_CLIENT_ID: Идентификатор клиента вашего Google OAuth приложения.
    GOOGLE_CLIENT_ID: str = Field(..., env="GOOGLE_CLIENT_ID", description="Client ID Google OAuth")
    
    # GOOGLE_CLIENT_SECRET: Секрет клиента вашего Google OAuth приложения.
    # Должен храниться в секрете!
    GOOGLE_CLIENT_SECRET: str = Field(..., env="GOOGLE_CLIENT_SECRET", description="Client Secret Google OAuth")
    
    # GOOGLE_REDIRECT_URI: URI перенаправления, который вы зарегистрировали в Google Cloud Console.
    # Куда Google будет отправлять пользователя после успешной аутентификации.
    GOOGLE_REDIRECT_URI: str = Field(..., env="GOOGLE_REDIRECT_URI", description="Redirect URI для Google OAuth")
    
    # GOOGLE_SCOPES: Области доступа (scopes), которые вы запрашиваете у пользователя Google.
    # openid: Обязательно для OpenID Connect.
    # email: Для получения email пользователя.
    # profile: Для получения базовой информации профиля (имя, изображение).
    GOOGLE_SCOPES: str = "openid email profile"

    # --- Настройки Spotify API (для доступа к музыке) ---
    # SPOTIFY_CLIENT_ID: Идентификатор клиента вашего приложения Spotify.
    SPOTIFY_CLIENT_ID: str = Field(..., env="SPOTIFY_CLIENT_ID", description="Client ID Spotify API")
    
    # SPOTIFY_CLIENT_SECRET: Секрет клиента вашего приложения Spotify.
    # Должен храниться в секрете!
    SPOTIFY_CLIENT_SECRET: str = Field(..., env="SPOTIFY_CLIENT_SECRET", description="Client Secret Spotify API")
    
    # SPOTIFY_REDIRECT_URI: URI перенаправления, который вы зарегистрировали в приложении Spotify.
    # Куда Spotify будет отправлять пользователя после успешной аутентификации.
    SPOTIFY_REDIRECT_URI: str = Field(..., env="SPOTIFY_REDIRECT_URI", description="Redirect URI для Spotify API")
    
    # SPOTIFY_SCOPES: Области доступа (scopes), которые вы запрашиваете у пользователя Spotify.
    # Эти скоупы позволят вашему приложению управлять воспроизведением и читать данные пользователя.
    SPOTIFY_SCOPES: str = (
        "user-read-private user-read-email "
        "user-top-read user-read-playback-state user-modify-playback-state "
        "playlist-read-private playlist-read-collaborative user-library-read "
        "streaming app-remote-control user-read-currently-playing"
    )

    # --- Настройки SMTP для отправки email (например, для подтверждения почты) ---
    # Если вы планируете отправлять email (например, для подтверждения email),
    # эти настройки будут необходимы.
    SMTP_HOST: str = Field("smtp.example.com", env="SMTP_HOST", description="SMTP хост для отправки email")
    SMTP_PORT: int = Field(587, env="SMTP_PORT", description="SMTP порт для отправки email")
    SMTP_USER: str = Field("user@example.com", env="SMTP_USER", description="Имя пользователя SMTP")
    SMTP_PASSWORD: str = Field("password", env="SMTP_PASSWORD", description="Пароль SMTP")
    SMTP_FROM_EMAIL: str = Field("noreply@example.com", env="SMTP_FROM_EMAIL", description="Email отправителя")
    SMTP_USE_TLS: bool = Field(True, env="SMTP_USE_TLS", description="Использовать TLS для SMTP")

    REDIS_HOST: str = Field(..., description="Хост Redis")
    REDIS_PORT: int = Field(6379, description="Порт Redis")
    REDIS_URL: str 

    RABBITMQ_BROKER_URL: str


    @property
    def sync_db_url(self) -> str:
        """
        Возвращает синхронный URL для подключения к базе данных.
        Используется, например, для Alembic.
        """
        return f'postgresql+psycopg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}'
    
    @property
    def async_db_url(self) -> str:
        """
        Возвращает асинхронный URL для подключения к базе данных.
        Используется, например, для FastAPI с AsyncSession.
        """
        return f'postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}'
    
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / '.env',
        extra='ignore'          
    )


settings = Settings()