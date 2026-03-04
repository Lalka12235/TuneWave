import uuid

from app.config.log_config import logger
from app.domain.interfaces.track_gateway import TrackGateway
from app.domain.entity import TrackEntity

from app.domain.exceptions.track_exception import TrackNotFound


class ReadTrack:
    def __init__(self, track_repo: TrackGateway):
        self.track_repo = track_repo

    def get_track_by_id(self, track_id: uuid.UUID) -> TrackEntity:
        """Получает трек по его UUID из базы данных."""
        track = self.track_repo.get_track_by_id(track_id)
        if not track:
            logger.warning(f"Сервис треков: Не удалось найти трек с ID '{track_id}'.")
            raise TrackNotFound()

        return track

    def get_track_by_Spotify_id(self, spotify_id: str) -> TrackEntity:
        """Получает трек по его Spotify ID из базы данных."""
        track = self.track_repo.get_track_by_spotify_id(spotify_id)
        if not track:
            logger.warning(
                f"Сервис треков: Не удалось найти трек с Spotify ID '{spotify_id}'."
            )
            raise TrackNotFound()

        return track