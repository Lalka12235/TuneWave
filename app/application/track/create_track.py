from app.config.log_config import logger
from app.domain.interfaces.track_gateway import TrackGateway
from app.domain.entity import TrackEntity


from app.domain.exceptions.exception import ServerError

class CreateTrack:

    def __init__(self, track_repo: TrackGateway):
        self.track_repo = track_repo

    def create_track(self, track_data: dict[str,str]) -> TrackEntity:
        """Создает новый трек в базе данных."""
        try:
            db_track = self.track_repo.create_track(track_data)
            logger.info(
                f"Сервис треков: Новый трек '{track_data['title']}' (Spotify ID: {track_data['spotify_id']}) создан в базе данных."
            )
            return db_track
        except Exception as e:
            logger.error(
                f"Сервис треков: Ошибка при создании трека '{track_data['spotify_id']}': {e}",
                exc_info=True,
            )
            raise ServerError(detail="Ошибка при создании трека")
    
    #todo recheck
    def get_or_create_track_from_spotify(
        self, spotify_data: dict[str,str]
    ) -> TrackEntity:
        """
        Пытается получить трек из кеша (БД) по Spotify ID. Если не найден,
        запрашивает его у Spotify API и сохраняет в кеше.
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
        new_local_track_response = self.create_track(spotify_data)
        logger.info(
            f"Сервис треков: Трек '{spotify_data['spotify_id']}' успешно получен от Spotify и кеширован в БД."
        )
        return new_local_track_response