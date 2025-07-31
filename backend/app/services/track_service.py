from fastapi import HTTPException,status
from app.repositories.track_repo import TrackRepository
from app.schemas.track_schemas import TrackResponse,TrackCreate
from sqlalchemy.orm import Session
from app.models.track import Track
import uuid



class TrackService:


    @staticmethod
    def _map_track_to_response(track: Track) -> TrackResponse:
        """Преобразует объект модели Track в Pydantic-схему TrackResponse."""
        return TrackResponse.model_validate(track)
    

    @staticmethod
    def get_track_by_id(db: Session,track_id: uuid.UUID) -> Track | None:
        """Получает трек по его UUID из базы данных."""
        track = TrackRepository.get_track_by_id(db,track_id)
        if not track:
            raise HTTPException(
                status_code=404,
                detail='Трек не найден'
            )
        
        return track
    

    @staticmethod
    def get_track_by_Spotify_id(db: Session,spotify_id: str) -> Track | None:
        """Получает трек по его Spotify ID из базы данных."""
        track = TrackRepository.get_track_by_spotify_id(db,spotify_id)
        if not track:
            raise HTTPException(
                status_code=404,
                detail='Трек не найден'
            )
        
        return track
    

    @staticmethod
    def create_track(db: Session,track_data: TrackCreate) -> Track:
        """Создает новый трек в базе данных."""
        db_track = TrackRepository.create_track(db,track_data)
        db.commit()
        db.refresh(db_track)
        return db_track
    

    @staticmethod
    def get_or_create_track_from_spotify_data(db: Session,spotify_track_data: dict) -> Track:
        """
        Получает трек по Spotify ID. Если трек не существует, создает его.
        Возвращает существующий или новый трек.
        """
        spotify_id = spotify_track_data.get('id')
        if not spotify_id:
            raise ValueError("Данные Spotify трека не содержат 'id'.")
        
        existing_track = TrackRepository.get_track_by_spotify_id(db, spotify_id)
        if existing_track:
            return existing_track
        
        artists = ", ".join([artist['name'] for artist in spotify_track_data.get('artists', [])])
        album_image_url = spotify_track_data.get('album', {}).get('images', [])[0].get('url') if spotify_track_data.get('album', {}).get('images') else None
        
        track_create_data = TrackCreate(
            spotify_id=spotify_id,
            title=spotify_track_data.get('name'),
            artist=artists,
            album=spotify_track_data.get('album', {}).get('name'),
            album_image_url=album_image_url,
            duration_ms=spotify_track_data.get('duration_ms'),
            external_url=spotify_track_data.get('external_urls', {}).get('spotify')
        )
        return TrackService.create_track(db, track_create_data)
    

    @staticmethod
    def delete_track(db: Session, track_id: uuid.UUID) -> bool:
        """Удаляет трек по его UUID."""
        return TrackRepository.delete_track(db, track_id)


    @staticmethod
    def get_all_tracks(db: Session) -> list[Track]:
        """Получает все треки из базы данных."""
        return TrackRepository.get_all_tracks(db)