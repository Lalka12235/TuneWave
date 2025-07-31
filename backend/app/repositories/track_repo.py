from sqlalchemy import select,delete
from sqlalchemy.orm import Session
from app.models.track import Track
from app.schemas.track_schemas import TrackCreate
import uuid


class TrackRepository:

    @staticmethod
    def get_track_by_id(db: Session,track_id: uuid.UUID) -> Track | None:
        """Получает трек по его UUID."""
        stmt = select(Track).where(
            Track.id == track_id,
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none()
    

    @staticmethod
    def get_track_by_spotify_id(db: Session,spotify_id: str) -> Track | None:
        """Получает трек по его Spotify ID."""
        stmt = select(Track).where(
            Track.spotify_track_id == spotify_id,
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none()
    

    @staticmethod
    def create_track(db: Session,track_data: TrackCreate) -> Track:
        """Создает новый трек в базе данных."""
        new_track = Track(**track_data.model_dump()) 
        db.add(new_track)
        db.flush()
        return new_track
    
    
    @staticmethod
    def delete_track(db: Session, track_id: uuid.UUID) -> bool:
        """Удаляет трек по его UUID."""
        stmt = delete(Track).where(
            Track.id == track_id,
        )
        result = db.execute(stmt)
        return result.rowcount > 0
    

    @staticmethod
    def get_all_tracks(db: Session) -> list[Track]:
        """Получает все треки из базы данных."""
        stmt = select(Track)
        result = db.execute(stmt)
        return result.scalars().all()
    

