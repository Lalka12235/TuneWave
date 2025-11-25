from pathlib import Path
from dotenv import load_dotenv
import os
from dataclasses import dataclass

BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(f'{BASE_DIR}/.env')


@dataclass(slots=True, frozen=True)
class DataBaseConfig:
    APP_CONFIG_DB_URL: str = os.getenv('APP_CONFIG_DB_URL')
    DB_HOST: str = os.getenv('DB_HOST')
    DB_PORT: int = os.getenv('DB_PORT')
    DB_USER: str = os.getenv('DB_USER')
    DB_PASS: str = os.getenv('DB_PASS')
    DB_NAME: str = os.getenv('DB_NAME')

    @property
    def sync_db_url(self) -> str:
        return f"postgresql+psycopg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @property
    def async_db_url(self) -> str:
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"


@dataclass(slots=True, frozen=True)
class GoogleConfig:
    GOOGLE_CLIENT_ID: str = os.getenv('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET: str = os.getenv('GOOGLE_CLIENT_SECRET')
    GOOGLE_REDIRECT_URI: str = os.getenv('GOOGLE_REDIRECT_URI')
    GOOGLE_SCOPES: str = os.getenv('GOOGLE_SCOPES')


@dataclass(slots=True, frozen=True)
class SpotifyConfig:
    SPOTIFY_CLIENT_ID: str = os.getenv('SPOTIFY_CLIENT_ID')
    SPOTIFY_CLIENT_SECRET: str = os.getenv('SPOTIFY_CLIENT_SECRET')
    SPOTIFY_REDIRECT_URI: str = os.getenv('SPOTIFY_REDIRECT_URI')
    SPOTIFY_SCOPES: str = os.getenv('SPOTIFY_SCOPES')


@dataclass(slots=True, frozen=True)
class JWTConfig:
    JWT_SECRET_KEY: str = os.getenv('JWT_SECRET_KEY')
    ALGORITHM: str = os.getenv('ALGORITHM')
    ACCESS_TOKEN_EXPIRE_MINUTES: int = os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES')


@dataclass(slots=True, frozen=True)
class SMTPConfig:
    SMTP_HOST: str = os.getenv('SMTP_HOST')
    SMTP_PORT: int = os.getenv('SMTP_PORT')
    SMTP_USER: str = os.getenv('SMTP_USER')
    SMTP_PASSWORD: str = os.getenv('SMTP_PASSWORD')
    SMTP_FROM_EMAIL: str = os.getenv('SMTP_FROM_EMAIL')
    SMTP_USE_TLS: bool = os.getenv('SMTP_USE_TLS')


@dataclass(slots=True, frozen=True)
class RedisConfig:
    REDIS_HOST: str = os.getenv('REDIS_HOST')
    REDIS_PORT: int = os.getenv('REDIS_PORT')
    REDIS_URL: str = os.getenv('REDIS_URL')


@dataclass(slots=True, frozen=True)
class RabbitConfig:
    RABBITMQ_BROKER_URL: str = os.getenv('RABBITMQ_BROKER_URL')


@dataclass(slots=True, frozen=True)
class AvatarConfig:
    AX_AVATAR_SIZE_BYTES: int = 5 * 1024 * 1024
    BACKEND_ROOT: Path = Path(__file__).resolve().parent.parent.parent
    AVATARS_STORAGE_DIR: Path = BACKEND_ROOT / "avatars"


@dataclass(slots=True, frozen=True)
class Settings:
    database: DataBaseConfig = DataBaseConfig()
    google: GoogleConfig = GoogleConfig()
    spotify: SpotifyConfig = SpotifyConfig()
    jwt: JWTConfig = JWTConfig()
    smtp: SMTPConfig = SMTPConfig()
    redis: RedisConfig = RedisConfig()
    rabbit: RabbitConfig = RabbitConfig()
    avatar: AvatarConfig = AvatarConfig()

    BASE_URL: str = "http://127.0.0.1:8000"


settings = Settings()