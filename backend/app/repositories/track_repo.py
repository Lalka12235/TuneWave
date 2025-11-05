from sqlalchemy import select,delete
from sqlalchemy.orm import Session
from app.models.track import Track
import uuid
from app.repositories.abc.abc_track_repo import ABCTrackRepository
from app.schemas.entity import TrackEntity


class TrackRepository(ABCTrackRepository):

    def __init__(self, db: Session):
        self._db = db

    def from_model_to_entity(self,model: Track | None) -> TrackEntity:
        return TrackEntity(
            id=model.id,
            spotify_id=model.spotify_id,
            spotify_uri=model.spotify_uri,
            title=model.title,
            artist_names=model.artist_names,
            album_name=model.album_name,
            album_cover_url=model.album_cover_url,
            duration_ms=model.duration_ms,
            is_playable=model.is_playable,
            spotify_track_url=model.spotify_track_url,
            last_synced_at=model.last_synced_at,
            created_at=model.created_at,
        )

    
    def get_track_by_id(self,track_id: uuid.UUID) -> TrackEntity | None:
        """Получает трек по его UUID."""
        stmt = select(Track).where(
            Track.id == track_id,
        )
        result = self._db.execute(stmt)
        result = result.scalar_one_or_none()
        return self.from_model_to_entity(result)
    

    def get_track_by_spotify_id(self,spotify_id: str) -> TrackEntity | None:
        """Получает трек по его Spotify ID."""
        stmt = select(Track).where(
            Track.spotify_id == spotify_id,
        )
        result = self._db.execute(stmt)
        result = result.scalar_one_or_none()
        return self.from_model_to_entity(result)
    
    def create_track(self,track_data: dict[str,str]) -> TrackEntity:
        """Создает новый трек в базе данных.""" 
        new_track = Track(**track_data)
        self._db.add(new_track)
        self._db.flush()
        return self.from_model_to_entity(new_track)
    
    
    def delete_track(self, track_id: uuid.UUID) -> bool:
        """Удаляет трек по его UUID."""
        stmt = delete(Track).where(
            Track.id == track_id,
        )
        result = self._db.execute(stmt)
        return result.rowcount > 0