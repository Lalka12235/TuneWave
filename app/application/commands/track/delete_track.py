import uuid

from app.config.log_config import logger
from app.domain.interfaces.track_gateway import TrackGateway

from app.domain.exceptions.exception import ServerError

class DeleteTrack:

    def __init__(self, track_repo: TrackGateway):
        self.track_repo = track_repo

    def delete_track(self, track_id: uuid.UUID) -> bool:
        """Удаляет трек по его UUID."""
        deleted_successfully = self.track_repo.delete_track(track_id)
        logger.info(
            f"Сервис треков: Трек с ID '{track_id}' успешно удален из базы данных."
        )
        return deleted_successfully
