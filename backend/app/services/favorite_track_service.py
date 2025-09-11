from fastapi import HTTPException,status
from sqlalchemy.orm import Session
from app.schemas.favorite_track_schemas import FavoriteTrackResponse
from app.models import FavoriteTrack
from app.repositories.favorite_track_repo import FavoriteTrackRepository
from app.repositories.track_repo import TrackRepository
from app.services.track_service import TrackService
import uuid
from typing import Any
from app.logger.log_config import logger


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
        logger.debug('FavoriteTrackService: Выполняет поиск любимых треков пользователя %s',str(user_id))
        
        if not favorite_tracks:
            logger.info('FavoriteTrackService: Любимых треков пользователя %s не найдено',str(user_id))
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
        track = await TrackService._get_or_create_track(db,spotify_id)
        
        is_favorite = FavoriteTrackRepository.is_favorite_track(db, user_id, track.id)
        if is_favorite:
            logger.warning('FavoriteTrackService: Этот трек %s уже добавлен у пользователя %s',str(track.id),str(user_id))
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail='Этот трек уже добавлен в ваш список любимых.'
            )
        try:
            new_favorite_track = FavoriteTrackRepository.add_favorite_track(db, user_id, track.id)
            db.info('FavoriteTrackService: Добавлен любимый трек %s пользователя %s в список',str(track.id),str(user_id))
            db.commit()
            db.refresh(new_favorite_track)
            return FavoriteTrackService._map_favorite_track_to_response(new_favorite_track)
        except HTTPException as e:
            logger.error('FavoriteTrackService: Произошла ошибка при добавление любимого трека %s пользователя %s. %r',str(track.id),str(user_id),e.detail,exc_info=True)
            db.rollback()
            raise e
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
        logger.debug('FavoriteTrackService: Делаем поиск в бд по Spotify ID %s',spotify_id)
        if not track:
            logger.warning('FavoriteTrackService: Трек с Spotify ID %s не удалось найти в базе данных',spotify_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Трек не найден в нашей базе данных."
            )

        is_favorite = FavoriteTrackRepository.is_favorite_track(db, user_id, track.id)
        if not is_favorite:
            logger.warning('FavoriteTrackService: Трек с Spotify ID %s не находиться в вашем списке любимых',spotify_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Этот трек не найден в вашем списке любимых."
            )
        try:
            removed_count = FavoriteTrackRepository.remove_favorite_track(db, user_id, track.id)
            logger.debug('FavoriteTrackService: Производим удаление любимого трека с Spotify ID %s у пользователя %s',spotify_id,str(user_id))
            if removed_count: 
                db.commit() 
                return {
                    'action': 'remove favorite track',
                    'status': 'success',
                    'detail': f'Трек {spotify_id} успешно удален из избранного.',
                }
            else:
                logger.error('FavoriteTrackService: Произошла ошибка при удаление любимого трека с Spotify ID %s у пользователя %s',spotify_id,str(user_id))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Не удалось удалить любимый трек."
                )
        except HTTPException as e:
            logger.error('FavoriteTrackService: Произошла ошибка при удаление любимого трека с Spotify ID %s у пользователя %s. %r',spotify_id,str(user_id),e.detail,exc_info=True)
            db.rollback()
            raise e
        except Exception:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Не удалось удалить любимый трек из-за внутренней ошибки сервера."
            )