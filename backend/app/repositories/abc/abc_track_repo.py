from abc import ABC,abstractmethod
import uuid
from app.schemas.entity import TrackEntity


class ABCTrackRepository(ABC):

    @abstractmethod
    def get_track_by_id(self,track_id: uuid.UUID) -> TrackEntity | None:
        """Получает трек по его UUID."""
        raise NotImplementedError()
    
    @abstractmethod
    def get_track_by_spotify_id(self,spotify_id: str) -> TrackEntity | None:
        """Получает трек по его Spotify ID."""
        raise NotImplementedError
    @abstractmethod
    def create_track(self,track_data: dict[str,str]) -> TrackEntity:
        """Создает новый трек в базе данных.""" 
        raise NotImplementedError()
    
    @abstractmethod
    def delete_track(self, track_id: uuid.UUID) -> bool:
        """Удаляет трек по его UUID."""
        raise NotImplementedError()