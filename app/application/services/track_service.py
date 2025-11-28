import uuid

from app.config.log_config import logger
from app.domain.interfaces.track_gateway import TrackGateway
from app.presentation.schemas.track_schemas import TrackResponse

from app.application.mappers.track_mapper import TrackMapper
from app.domain.exceptions.track_exception import TrackNotFound
from app.domain.exceptions.exception import ServerError

class TrackService:
    """
    Реализует бизнес логику для работы с треками
    """

    def __init__(self, track_repo: TrackGateway, track_mapper: TrackMapper):
        self.track_repo = track_repo
        self.track_mapper = track_mapper

    def get_track_by_id(self, track_id: uuid.UUID) -> TrackResponse:
        """Получает трек по его UUID из базы данных."""
        track = self.track_repo.get_track_by_id(track_id)
        if not track:
            logger.warning(f"Сервис треков: Не удалось найти трек с ID '{track_id}'.")
            raise TrackNotFound()

        return self.track_mapper.to_response_track(track)

    def get_track_by_Spotify_id(self, spotify_id: str) -> TrackResponse:
        """Получает трек по его Spotify ID из базы данных."""
        track = self.track_repo.get_track_by_spotify_id(spotify_id)
        if not track:
            logger.warning(
                f"Сервис треков: Не удалось найти трек с Spotify ID '{spotify_id}'."
            )
            raise TrackNotFound()

        return self.track_mapper.to_response_track(track)

    def create_track(self, track_data: dict[str,str]) -> TrackResponse:
        """Создает новый трек в базе данных."""
        try:
            db_track = self.track_repo.create_track(track_data)
            logger.info(
                f"Сервис треков: Новый трек '{track_data['title']}' (Spotify ID: {track_data['spotify_id']}) создан в базе данных."
            )
            return self.track_mapper.to_response(db_track)
        except Exception as e:
            logger.error(
                f"Сервис треков: Ошибка при создании трека '{track_data['spotify_id']}': {e}",
                exc_info=True,
            )
            raise ServerError(detail="Ошибка при создании трека")

    async def get_or_create_track_from_spotify(
        self, spotify_data: dict[str,str]
    ) -> TrackResponse:
        """
        Пытается получить трек из кеша (БД) по Spotify ID. Если не найден,
        запрашивает его у Spotify API и сохраняет в кеше.
        Возвращает объект TrackResponse.
        """
        local_track = self.track_repo.get_track_by_spotify_id(spotify_data['spotify_id'])
        if local_track:
            logger.debug(
                f"Сервис треков: Трек '{spotify_data['spotify_id']}' найден в локальном кеше."
            )
            return self.track_mapper.to_response_track(local_track)

        logger.info(
            f"Сервис треков: Трек '{spotify_data['spotify_id']}' не найден в кеше, запрашиваем у Spotify API."
        )
        try: # This should call self.create_track, not TrackService.create_track
            new_local_track_response = TrackService.create_track(spotify_data)
            logger.info(
                f"Сервис треков: Трек '{spotify_data['spotify_id']}' успешно получен от Spotify и кеширован в БД."
            )
            return self.track_mapper.to_response_track(new_local_track_response)
        except Exception as e:
            logger.error(
                f"Сервис треков: Неизвестная ошибка при получении/сохранении трека '{spotify_data['spotify_id']}': {e}",
                exc_info=True,
            )
            raise ServerError(
                detail="Не удалось получить или сохранить трек из-за внутренней ошибки"
            )

    def delete_track(self, track_id: uuid.UUID) -> bool:
        """Удаляет трек по его UUID."""
        track = self.track_repo.get_track_by_id(track_id)
        if not track:
            logger.warning(
                f"Сервис треков: Попытка удалить несуществующий трек с ID '{track_id}'."
            )
            raise TrackNotFound(
                detail=f"Трек с ID '{track_id}' не найден для удаления."
            )
        try:
            deleted_successfully = self.track_repo.delete_track(track_id)
            if deleted_successfully:
                logger.info(
                    f"Сервис треков: Трек с ID '{track_id}' успешно удален из базы данных."
                )
            else:
                logger.warning(
                    f"Сервис треков: Не удалось удалить трек с ID '{track_id}' из репозитория."
                )
                raise ServerError(detail=f"Не удалось удалить трек с ID '{track_id}'.")
            return deleted_successfully
        except Exception as e:
            logger.error(
                f"Сервис треков: Ошибка при удалении трека с ID '{track_id}': {e}",
                exc_info=True,
            )
            raise ServerError(detail="Ошибка при удалении трека.")
