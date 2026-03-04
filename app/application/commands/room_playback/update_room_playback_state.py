import uuid

from app.config.log_config import logger
from app.domain.interfaces.member_room_association import MemberRoomAssociationGateway
from app.domain.interfaces.room_gateway import RoomGateway
from app.domain.interfaces.room_track_association_gateway import RoomTrackAssociationGateway
from app.domain.interfaces.user_gateway import UserGateway

from app.presentation.schemas.room_schemas import RoomResponse
from app.presentation.schemas.spotify_schemas import SpotifyTrackDetails


from app.infrastructure.ws.manager_notify_service import NotifyService

from app.domain.exceptions.exception import ServerError
from app.domain.exceptions.room_exception import RoomNotFoundError



class UpdateRoomPlaybackState:
    def __init__(
        self,
        user_repo: UserGateway,
        room_track_repo: RoomTrackAssociationGateway,
        room_repo: RoomGateway,
        member_room_repo: MemberRoomAssociationGateway,
        notify_service: NotifyService,
    ):
        self.user_repo = user_repo
        self.room_track_repo = room_track_repo
        self.room_repo = room_repo
        self.member_room_repo = member_room_repo
        self.notify_service = notify_service

    async def update_room_playback_state(
        self,
        room_id: uuid.UUID,
        current_playing_track_assoc_id: uuid.UUID | None,
        progress_ms: int,
        is_playing: bool,
    ) -> RoomResponse:
        """
        Обновляет состояние воспроизведения в полях комнаты.
        """
        room = self.room_repo.get_room_by_id(room_id)
        if not room:
            logger.warning(f"RoomService: Комната с такпим id {room_id} не найдена")
            raise RoomNotFoundError()

        room.current_playing_track_association_id = current_playing_track_assoc_id
        room.current_track_position_ms = progress_ms
        room.is_playing = is_playing

        try:
            logger.debug(
                f"RoomService: Обновлено состояние воспроизведения для комнаты '{room_id}'. Трек: '{current_playing_track_assoc_id}', Прогресс: {progress_ms}ms, Играет: {is_playing}."
            )
        except Exception as e:
            logger.error(
                f"RoomService: Ошибка при обновлении состояния воспроизведения для комнаты '{room_id}': {e}",
                exc_info=True,
            )
            raise ServerError(
                detail="Не удалось обновить состояние воспроизведения комнаты."
            )

        current_track_details: SpotifyTrackDetails | None = None
        current_track_assoc = None
        if current_playing_track_assoc_id:
            current_track_assoc = self.room_track_repo.get_association_by_id(
                current_playing_track_assoc_id
            )
            if current_track_assoc and current_track_assoc.track:
                current_track_details = SpotifyTrackDetails.model_validate(
                    current_track_assoc.track
                )

        await self.notify_service.send_mesasge_for_user(
            {
            "action": "player_state_changed",
            "room_id": str(room_id),
            "is_playing": is_playing,
            "current_track_association_id": (
                str(current_playing_track_assoc_id)
                if current_playing_track_assoc_id
                else None
            ),
            "current_track": (
                current_track_details.model_dump() if current_track_details else None
            ),
            "progress_ms": progress_ms,
            "duration_ms": (
                current_track_assoc.track.duration_ms
                if current_track_assoc and current_track_assoc.track
                else 0
            ),
            }
        )
        
        logger.debug(
            f"RoomService: Отправлено WS-уведомление об изменении состояния плеера в комнате '{room_id}'."
        )
        return room