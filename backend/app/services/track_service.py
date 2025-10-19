import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.logger.log_config import logger
from app.models.track import Track
from app.repositories.track_repo import TrackRepository
from app.schemas.track_schemas import TrackCreate, TrackResponse
from app.services.spotify_public_service import SpotifyPublicService


class TrackService:

    def __init__(self,db: Session,track_repo: TrackRepository):
        self._db = db
        self.track_repo = track_repo


    @staticmethod
    def _map_track_to_response(self,track: Track) -> TrackResponse:
        """Преобразует объект модели Track в Pydantic-схему TrackResponse."""
        return TrackResponse.model_validate(track)
    

    
    def get_track_by_id(self,track_id: uuid.UUID) -> TrackResponse:
        """Получает трек по его UUID из базы данных."""
        track = self.track_repo.get_track_by_id(track_id)
        if not track:
            logger.warning(f"Сервис треков: Не удалось найти трек с ID '{track_id}'.")
            raise HTTPException(
                status_code=404,
                detail='Трек не найден'
            )
        
        return track
    

    
    def get_track_by_Spotify_id(self,spotify_id: str) -> TrackResponse:
        """Получает трек по его Spotify ID из базы данных."""
        track = self.track_repo.get_track_by_spotify_id(spotify_id)
        if not track:
            logger.warning(f"Сервис треков: Не удалось найти трек с Spotify ID '{spotify_id}'.")
            raise HTTPException(
                status_code=404,
                detail='Трек не найден'
            )
        
        return track
    

    
    def create_track(self,track_data: TrackCreate) -> TrackResponse:
        """Создает новый трек в базе данных."""
        try:
            db_track = self.track_repo.create_track(track_data)
            self._db.commit()
            self._db.refresh(db_track)
            logger.info(f"Сервис треков: Новый трек '{track_data.title}' (Spotify ID: {track_data.spotify_id}) создан в базе данных.")
            return db_track
        except Exception as e:
            self._db.rollback()
            logger.error(f"Сервис треков: Ошибка при создании трека '{track_data.spotify_id}': {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ошибка при создании трека"
            )
    

    
    async def get_or_create_track_from_spotify(self, spotify_data: TrackCreate) -> TrackResponse:
        """
        Пытается получить трек из кеша (БД) по Spotify ID. Если не найден,
        запрашивает его у Spotify API и сохраняет в кеше.
        Возвращает объект TrackResponse.
        """
        local_track = self.track_repo.get_track_by_spotify_id( spotify_data.spotify_id)
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
            new_local_track_response = TrackService.create_track( spotify_data)
            self._db.commit()
            self._db.refresh(new_local_track_response)
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
    

    
    def delete_track(self, track_id: uuid.UUID) -> bool:
        """Удаляет трек по его UUID."""
        track = self.track_repo.get_track_by_id( track_id)
        if not track:
            logger.warning(f"Сервис треков: Попытка удалить несуществующий трек с ID '{track_id}'.")
            raise HTTPException(status_code=404,detail=f"Трек с ID '{track_id}' не найден для удаления.")
        try:
            deleted_successfully = self.track_repo.delete_track( track_id)
            if deleted_successfully:
                self._db.commit()
                logger.info(f"Сервис треков: Трек с ID '{track_id}' успешно удален из базы данных.")
            else:
                self._db.rollback()
                logger.warning(f"Сервис треков: Не удалось удалить трек с ID '{track_id}' из репозитория.")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Не удалось удалить трек с ID '{track_id}'."
                )
            return deleted_successfully
        except HTTPException as e:
            self._db.rollback()
            raise e
        except Exception as e:
            self._db.rollback()
            logger.error(f"Сервис треков: Ошибка при удалении трека с ID '{track_id}': {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ошибка при удалении трека."
            )