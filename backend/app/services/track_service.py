from fastapi import HTTPException,status
from app.repositories.track_repo import TrackRepository
from app.schemas.track_schemas import TrackResponse,TrackCreate
from sqlalchemy.orm import Session
from app.models import Track,User
from app.services.spotify_public_service import SpotifyPublicService
from app.services.spotify_sevice import SpotifyService
import uuid
from app.logger.log_config import logger


class TrackService:


    @staticmethod
    def _map_track_to_response(track: Track) -> TrackResponse:
        """Преобразует объект модели Track в Pydantic-схему TrackResponse."""
        return TrackResponse.model_validate(track)
    

    @staticmethod
    def get_track_by_id(db: Session,track_id: uuid.UUID) -> TrackResponse:
        """Получает трек по его UUID из базы данных."""
        track = TrackRepository.get_track_by_id(db,track_id)
        if not track:
            logger.warning(f"Сервис треков: Не удалось найти трек с ID '{track_id}'.")
            raise HTTPException(
                status_code=404,
                detail='Трек не найден'
            )
        
        return track
    

    @staticmethod
    def get_track_by_Spotify_id(db: Session,spotify_id: str) -> TrackResponse:
        """Получает трек по его Spotify ID из базы данных."""
        track = TrackRepository.get_track_by_spotify_id(db,spotify_id)
        if not track:
            logger.warning(f"Сервис треков: Не удалось найти трек с Spotify ID '{spotify_id}'.")
            raise HTTPException(
                status_code=404,
                detail='Трек не найден'
            )
        
        return track
    

    @staticmethod
    def create_track(db: Session,track_data: TrackCreate) -> TrackResponse:
        """Создает новый трек в базе данных."""
        exist_track = TrackRepository.get_track_by_spotify_id(db,track_data.spotify_id)
        if exist_track:
            logger.error()
            raise HTTPException(
                status_code=409,
                detail='Такой трек уже существует в базе данных'
            )
        try:
            db_track = TrackRepository.create_track(db,track_data)
            db.commit()
            db.refresh(db_track)
            logger.info(f"Сервис треков: Новый трек '{track_data.title}' (Spotify ID: {track_data.spotify_id}) создан в базе данных.")
            return db_track
        except Exception as e:
            db.rollback()
            logger.error(f"Сервис треков: Ошибка при создании трека '{track_data.spotify_id}': {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ошибка при создании трека"
            )
    

    @staticmethod
    async def get_or_create_track(db: Session, spotify_id: str,current_user: User | None = None) -> TrackResponse:
        """
        Ищет трек в нашей базе данных по Spotify ID. Если не находит,
        получает информацию о треке из Spotify API и сохраняет его в нашей БД.

        Args:
            db (Session): Сессия базы данных.
            spotify_id (str): Уникальный Spotify ID трека.

        Returns:
            TrackResponse: Схема возращаемых данных о треке.

        Raises:
            HTTPException: Если трек не найден в Spotify или произошла ошибка при его создании.
        """
        track = TrackRepository.get_track_by_spotify_id(db, spotify_id)
        if track:
            logger.info(f'FavoriteTrackSevice: Трек найден в базе данных с ID {spotify_id}')
            return track 
        

        spotify_detail: dict = dict()
        if current_user and current_user.spotify_access_token:
            logger.info(f'FavoriteTrackSevice: У пользователя {current_user.id} найдены токены Spotify. Выполняем поиск трека {spotify_id} через токены пользователя')
            spotify_user_service = SpotifyService(db,current_user)
            spotify_detail = await spotify_user_service.search_track_by_spotify_id(spotify_id)
        else:
            logger.info(f'FavoriteTrackSevice: У пользователя {current_user.id} не найдены токены Spotify. Выполняем поиск трека {spotify_id} через публичные токены')
            spotify_public_service = SpotifyPublicService()
            spotify_detail = await spotify_public_service.search_track_by_spotify_id(spotify_id)

                
        if not spotify_detail:
            logger.error(f'FavoriteTrackSevice: Данные о треки не найдены или сам трек {spotify_id}')
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Трек с Spotify ID '{spotify_id}' не найден на Spotify."
            )
        try:
            track_create_data = TrackCreate(**spotify_detail)
            new_track = TrackRepository.create_track(db, track_create_data)
            logger.info('TrackService: Создаем трек с Spotify ID %s в базе данных',track_create_data.spotify_id)
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
    def delete_track(db: Session, track_id: uuid.UUID) -> bool:
        """Удаляет трек по его UUID."""
        track = TrackRepository.get_track_by_id(db, track_id)
        if not track:
            logger.warning(f"Сервис треков: Попытка удалить несуществующий трек с ID '{track_id}'.")
            raise HTTPException(status_code=404,detail=f"Трек с ID '{track_id}' не найден для удаления.")
        try:
            deleted_successfully = TrackRepository.delete_track(db, track_id)
            if deleted_successfully:
                db.commit()
                logger.info(f"Сервис треков: Трек с ID '{track_id}' успешно удален из базы данных.")
            else:
                db.rollback()
                logger.warning(f"Сервис треков: Не удалось удалить трек с ID '{track_id}' из репозитория.")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Не удалось удалить трек с ID '{track_id}'."
                )
            return deleted_successfully
        except HTTPException as e:
            db.rollback()
            raise e
        except Exception as e:
            db.rollback()
            logger.error(f"Сервис треков: Ошибка при удалении трека с ID '{track_id}': {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ошибка при удалении трека."
            )