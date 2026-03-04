import uuid

from app.config.log_config import logger
from app.domain.interfaces.room_gateway import RoomGateway

from app.presentation.schemas.room_schemas import RoomResponse

from app.infrastructure.ws.manager_notify_service import NotifyService

from app.domain.exceptions.exception import ServerError


class ClearPlaybackState:
    def __init__(
        self,
        room_repo: RoomGateway,
        notify_service: NotifyService,
    ):
        self.room_repo = room_repo
        self.notify_service = notify_service


    async def clear_playback_host(self, room_id: uuid.UUID) -> RoomResponse:
        """
        Очищает хоста воспроизведения для комнаты и сбрасывает состояние плеера.
        """
        room = self.room_repo.get_room_by_id(room_id)
        if not room.playback_host_id:
            logger.info(
                f"RoomService: Для комнаты '{room_id}' нет активного хоста воспроизведения для сброса."
            )
            return room

        old_host_id = room.playback_host_id

        try:
            room.playback_host_id = None
            room.active_spotify_device_id = None
            room.is_playing = False
            room.current_track_id = None
            room.current_track_position_ms = 0
            logger.info(
                f"RoomService: Хост воспроизведения для комнаты '{room_id}' (бывший хост: '{old_host_id}') успешно очищен."
            )
        except Exception as e:
            logger.error(
                f"RoomService: Ошибка при очистке хоста воспроизведения для комнаты '{room_id}': {e}",
                exc_info=True,
            )
            raise ServerError(detail="Не удалось очистить хоста воспроизведения.")

        await self.notify_service.send_mesasge_for_user(
            {
            "action": "playback_host_cleared",
            "room_id": str(room_id),
            "old_playback_host_id": str(old_host_id) if old_host_id else None,
            "message": "Хост воспроизведения комнаты был сброшен.",
            }
        )
        logger.info(
            f"RoomService: Отправлено WS-уведомление об очистке хоста воспроизведения в комнате '{room_id}'."
        )
        return room
