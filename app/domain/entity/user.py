from dataclasses import dataclass
import uuid

@dataclass(slots=True,frozen=True)
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
    spotify_id: str
    spotify_profile_url: str
    spotify_image_url: str