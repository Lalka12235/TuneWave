from fastapi import HTTPException,status
from sqlalchemy.orm import Session
from app.schemas.favorite_track_schemas import FavoriteTrackResponse
from app.schemas.track_schemas import TrackCreate
from app.models.favorite_track import FavoriteTrack
from app.repositories.favorite_track_repo import FavoriteTrackRepository
from app.services.spotify_sevice import SpotifyService
from app.repositories.track_repo import TrackRepository
from app.models.track import Track
from app.services.spotify_public_service import SpotifyPublicService
import uuid
from typing import Any
from app.models.user import User


class FavoriteTrackService:

    @staticmethod
    def _map_favorite_track_to_response(favorite_track_model: FavoriteTrack) -> FavoriteTrackResponse:
        """
        Вспомогательный метод для преобразования объекта FavoriteTrack SQLAlchemy
        в Pydantic FavoriteTrackResponse.
        
        Args:
            favorite_track_model (FavoriteTrack): ORM-объект FavoriteTrack,
                                                 включающий связанный объект Track.
                                                 
        Returns:
            FavoriteTrackResponse: Pydantic-модель FavoriteTrackResponse.
        """
        return FavoriteTrackResponse.model_validate(favorite_track_model)
    
    @staticmethod
    async def _get_or_create_track(db: Session, spotify_id: str,current_user: User | None = None) -> Track:
        """
        Ищет трек в нашей базе данных по Spotify ID. Если не находит,
        получает информацию о треке из Spotify API и сохраняет его в нашей БД.

        Args:
            db (Session): Сессия базы данных.
            spotify_id (str): Уникальный Spotify ID трека.

        Returns:
            Track: Объект Track из нашей базы данных.

        Raises:
            HTTPException: Если трек не найден в Spotify или произошла ошибка при его создании.
        """
        spotify_detail = ''
        if current_user and current_user.spotify_access_token:
            spotify_user_service = SpotifyService(db,current_user)
            spotify_detail = await spotify_user_service.search_track_by_spotify_id(spotify_id)

        if not spotify_detail:
                spotify_public_service = SpotifyPublicService()
                spotify_detail = await spotify_public_service.search_track_by_spotify_id(spotify_id)

        
        track = TrackRepository.get_track_by_spotify_id(db, spotify_id)
        if track:
            return track 
                  
        if not spotify_detail:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Трек с Spotify ID '{spotify_id}' не найден на Spotify."
            )
        try:
            track_create_data = TrackCreate(**spotify_detail)

            new_track = TrackRepository.create_track(db, track_create_data)
            db.commit() 
            db.refresh(new_track) 
            return new_track

        except HTTPException as e:
            db.rollback() 
            raise e
        except Exception as e:
            db.rollback() 
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Ошибка сервера при обработке трека из Spotify: {e}"
            )

    @staticmethod
    def get_user_favorite_tracks(db: Session, user_id: uuid.UUID) -> list[FavoriteTrackResponse]:
        """
        Получает список всех любимых треков для указанного пользователя.

        Args:
            db (Session): Сессия базы данных.
            user_id (uuid.UUID): Уникальный ID пользователя.

        Returns:
            list[FavoriteTrackResponse]: Список Pydantic-моделей FavoriteTrackResponse.
        
        Raises:
            HTTPException: Если произошла ошибка при получении данных из БД.
        """
        favorite_tracks = FavoriteTrackRepository.get_favorite_tracks(db, user_id) 
        
        if not favorite_tracks:
            return []
        
        return [FavoriteTrackService._map_favorite_track_to_response(ft) for ft in favorite_tracks]
    
    @staticmethod
    async def add_favorite_track(db: Session, user_id: uuid.UUID, spotify_id: str) -> FavoriteTrackResponse:
        """
        Добавляет трек в список любимых треков пользователя.
        Сначала проверяет, существует ли трек в нашей БД, иначе создает его.
        Затем проверяет, не добавлен ли уже трек в избранное.

        Args:
            db (Session): Сессия базы данных.
            user_id (uuid.UUID): ID пользователя, добавляющего трек.
            spotify_id (str): Spotify ID трека.

        Returns:
            FavoriteTrackResponse: Pydantic-модель добавленного любимого трека.

        Raises:
            HTTPException: Если трек уже добавлен или произошла ошибка.
        """
        track = await FavoriteTrackService._get_or_create_track(db,spotify_id)
        
        is_favorite = FavoriteTrackRepository.is_favorite_track(db, user_id, track.id)
        if is_favorite:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail='Этот трек уже добавлен в ваш список любимых.'
            )
        try:
            new_favorite_track = FavoriteTrackRepository.add_favorite_track(db, user_id, track.id)
            db.commit()
            db.refresh(new_favorite_track)
            return FavoriteTrackService._map_favorite_track_to_response(new_favorite_track)

        except HTTPException:
            db.rollback()
            raise 
        except Exception:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Не удалось добавить любимый трек из-за внутренней ошибки сервера."
            )
    
    @staticmethod
    def remove_favorite_track(db: Session, user_id: uuid.UUID, spotify_id: str) -> dict[str, Any]:
        """
        Удаляет трек из списка любимых треков пользователя.

        Args:
            db (Session): Сессия базы данных.
            user_id (uuid.UUID): ID пользователя, удаляющего трек.
            spotify_id (str): Spotify ID трека.

        Returns:
            dict[str, Any]: Сообщение об успешном удалении.

        Raises:
            HTTPException: Если трек не найден в избранном пользователя или произошла ошибка.
        """
        
        track = TrackRepository.get_track_by_spotify_id(db, spotify_id)
        if not track:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Трек не найден в нашей базе данных."
            )

        is_favorite = FavoriteTrackRepository.is_favorite_track(db, user_id, track.id)
        if not is_favorite:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Этот трек не найден в вашем списке любимых."
            )
        try:
            removed_count = FavoriteTrackRepository.remove_favorite_track(db, user_id, track.id)
            db.commit() 
        
            if removed_count: 
                return {
                    'action': 'remove favorite track',
                    'status': 'success',
                    'detail': f'Трек {spotify_id} успешно удален из избранного.',
                }
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Не удалось удалить любимый трек."
                )

        except HTTPException as e:
            db.rollback()
            raise e
        except Exception:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Не удалось удалить любимый трек из-за внутренней ошибки сервера."
            )