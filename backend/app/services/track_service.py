from fastapi import HTTPException,status
from app.repositories.track_repo import TrackRepository
from app.schemas.track_schemas import TrackResponse,TrackCreate
from sqlalchemy.orm import Session
from app.models.track import Track
from app.services.spotify_public_service import SpotifyPublicService
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
    async def get_or_create_track_from_spotify(db: Session, spotify_data: TrackCreate) -> TrackResponse:
        """
        Пытается получить трек из кеша (БД) по Spotify ID. Если не найден,
        запрашивает его у Spotify API и сохраняет в кеше.
        Возвращает объект TrackResponse.
        """
        local_track = TrackRepository.get_track_by_spotify_id(db, spotify_data.spotify_id)
        if local_track:
            logger.debug(f"Сервис треков: Трек '{spotify_data.spotify_id}' найден в локальном кеше.")
            return TrackService._map_track_to_response(local_track)

        logger.info(f"Сервис треков: Трек '{spotify_data.spotify_id}' не найден в кеше, запрашиваем у Spotify API.")
        SpotifyPublicService()
        try:
            #spotify_track_details: SpotifyTrackDetails | None = await spotify_public_service.search_public_track(spotify_data.spotify_id)
            #if not spotify_track_details:
            #    logger.warning(f"Сервис треков: Трек '{spotify_data.spotify_id}' не найден в Spotify API.")
            #    raise HTTPException(status_code=404,detail=f"Трек с Spotify ID '{spotify_data.spotify_id}' не найден на Spotify.")
            new_local_track_response = TrackService.create_track(db, spotify_data)
            db.commit()
            db.refresh(new_local_track_response)
            logger.info(f"Сервис треков: Трек '{spotify_data.spotify_id}' успешно получен от Spotify и кеширован в БД.")
            return TrackService._map_track_to_response(new_local_track_response)
        except HTTPException as e:
            raise e
        except Exception as e:
            logger.error(f"Сервис треков: Неизвестная ошибка при получении/сохранении трека '{spotify_data.spotify_id}': {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Не удалось получить или сохранить трек из-за внутренней ошибки"
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

    #пересмотреть
    #@staticmethod
    #def get_all_tracks(db: Session) -> list[Track]:
    #    """Получает все треки из базы данных."""
    #    logger.info('Возвращаем')
    #    return TrackRepository.get_all_tracks(db)