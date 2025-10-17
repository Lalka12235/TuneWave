from sqlalchemy import select,delete
from sqlalchemy.orm import Session
from app.models.track import Track
from app.schemas.track_schemas import TrackCreate
import uuid


class TrackRepository:

    def __init__(self, db: Session):
        self.self = db

    
    def get_track_by_id(self,track_id: uuid.UUID) -> Track | None:
        """Получает трек по его UUID."""
        stmt = select(Track).where(
            Track.id == track_id,
        )
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()
    

    
    def get_track_by_spotify_id(self,spotify_id: str) -> Track | None:
        """Получает трек по его Spotify ID."""
        stmt = select(Track).where(
            Track.spotify_id == spotify_id,
        )
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()
    

    
    def create_track(self,track_data: TrackCreate) -> Track:
        """Создает новый трек в базе данных."""
        new_track = Track(**track_data.model_dump()) 
        self.db.add(new_track)
        self.db.flush()
        return new_track
    
    
    
    def delete_track(self, track_id: uuid.UUID) -> bool:
        """Удаляет трек по его UUID."""
        stmt = delete(Track).where(
            Track.id == track_id,
        )
        result = self.db.execute(stmt)
        return result.rowcount > 0
    

    
    def get_all_tracks(self) -> list[Track]:
        """Получает все треки из базы данных."""
        stmt = select(Track)
        result = self.db.execute(stmt)
        return result.scalars().all()
    

