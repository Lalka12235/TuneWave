from dataclasses import dataclass
import uuid

@dataclass
class UserEntity:
    """
    Сущность модели User
    """
    id: uuid.UUID
    username: str
    email: str
    is_email_verified: bool
    avatar_url: str
    bio: str
    google_id: str
    google_image_url: str
    google_access_token: str
    google_refresh_token: str
    google_token_expires_at: int
    spotify_id: str
    spotify_profile_url: str
    spotify_image_url: str
    spotify_access_token: str
    spotify_refresh_token: str
    spotify_token_expires_at: str