from pydantic import BaseModel,Field,EmailStr
import uuid


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Имя пользователя")
    email: EmailStr = Field(..., description="Email пользователя")
    is_email_verified: bool = Field(False, description="Подтвержден ли email")

class UserResponse(UserBase):
    id: uuid.UUID = Field(..., description="Уникальный ID пользователя")
    bio: str | None = Field(None,description='Описание профиля пользователя')
    avatar_url: str | None = Field(None,description='Аватар пользователя в профиле')
    google_id: str | None = Field(None, description="Google ID пользователя")
    google_image_url: str | None = Field(None, description="URL изображения профиля Google")
    spotify_id: str | None = Field(None, description="Spotify ID пользователя")
    spotify_profile_url: str | None = Field(None, description="URL профиля Spotify")
    spotify_image_url: str | None = Field(None, description="URL изображения профиля Spotify")
    
    class Config:
        # from_attributes = True (ранее orm_mode = True) позволяет Pydantic читать данные из ORM-моделей SQLAlchemy
        # Это очень удобно, так как Pydantic автоматически преобразует объект User SQLAlchemy в UserResponse Pydantic.
        from_attributes = True 


class UserCreate(UserBase):
    # Google-специфичные поля (могут быть None, если вход через Spotify)
    google_id: str | None = Field(None, description="Google ID пользователя")
    google_image_url: str | None = Field(None, description="URL изображения профиля Google")

    # Spotify-специфичные поля (могут быть None, если вход через Google)
    spotify_id: str | None = Field(None, description="Spotify ID пользователя")
    spotify_profile_url: str | None = Field(None, description="URL профиля Spotify")
    spotify_image_url: str | None = Field(None, description="URL изображения профиля Spotify")
    spotify_access_token: str | None = Field(None, description="Токен доступа Spotify")
    spotify_refresh_token: str | None = Field(None, description="Токен обновления Spotify")
    spotify_token_expires_at: int | None = Field(None, description="Время истечения токена Spotify (Unix timestamp)")

class UserUpdate(BaseModel):
    username: str | None = Field(None, min_length=3, max_length=50, description="Новое имя пользователя")
    email: EmailStr | None = Field(None, description="Новый email пользователя")
    is_email_verified: bool | None = Field(None, description="Новый статус подтверждения email")
    bio: str | None = Field(None,description='Описание профиля пользователя',max_length=1000)
    avatar_url: str | None = Field(None,description='Аватар пользователя в профиле')
    google_image_url: str | None = Field(None, description="Новый URL изображения профиля Google")
    spotify_profile_url: str | None = Field(None, description="Новый URL профиля Spotify")
    spotify_image_url: str | None = Field(None, description="Новый URL изображения профиля Spotify")
    spotify_access_token: str | None = Field(None, description="Новый токен доступа Spotify")
    spotify_refresh_token: str | None = Field(None, description="Новый токен обновления Spotify")
    spotify_token_expires_at: str | None = Field(None, description="Новое время истечения токена Spotify")


# Схема для данных, полученных от Google OAuth (входные данные для сервиса)
class GoogleOAuthData(BaseModel):
    email: EmailStr = Field(..., description="Email пользователя от Google")
    username: str = Field(..., description="Имя пользователя от Google")
    google_id: str = Field(..., description="Google ID пользователя")
    google_image_url: str | None = Field(None, description="URL изображения профиля Google")
    is_email_verified: bool = Field(False, description="Подтвержден ли email от Google")
    google_access_token: str = Field(...,description='Токен доступа Google')
    google_refresh_token: str = Field(...,description='Токен обновления Google')
    google_token_expires_at: int = Field(...,description='Время истечения токена Google (Unix timestamp)')

# Схема для данных, полученных от Spotify OAuth (входные данные для сервиса)
class SpotifyOAuthData(BaseModel):
    email: EmailStr = Field(..., description="Email пользователя от Spotify")
    username: str = Field(..., description="Имя пользователя от Spotify")
    spotify_id: str = Field(..., description="Spotify ID пользователя")
    spotify_profile_url: str | None = Field(None, description="URL профиля Spotify")
    spotify_image_url: str | None = Field(None, description="URL изображения профиля Spotify")
    spotify_access_token: str = Field(..., description="Токен доступа Spotify")
    spotify_refresh_token: str = Field(..., description="Токен обновления Spotify")
    spotify_token_expires_at: int = Field(..., description="Время истечения токена Spotify (Unix timestamp)")
    spotify_scope: str = Field(..., description="Предоставленные скоупы Spotify")


class Token(BaseModel):
    access_token: str = Field(..., description="Токен доступа")
    token_type: str = Field("bearer", description="Тип токена")