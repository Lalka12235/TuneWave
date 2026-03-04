import uuid

from app.config.log_config import logger
from app.domain.entity.user import UserEntity
from app.domain.interfaces.member_room_association import MemberRoomAssociationGateway
from app.domain.interfaces.room_gateway import RoomGateway
from app.domain.interfaces.room_track_association_gateway import RoomTrackAssociationGateway
from app.domain.interfaces.user_gateway import UserGateway

from app.presentation.schemas.spotify_schemas import SpotifyTrackDetails

from app.domain.exceptions.exception import ServerError
from app.domain.exceptions.room_exception import (
    UserNotInRoomError,
    RoomNotFoundError,
)


class ReadPlayerState:
    def __init__(
        self,
        user_repo: UserGateway,
        room_track_repo: RoomTrackAssociationGateway,
        room_repo: RoomGateway,
        member_room_repo: MemberRoomAssociationGateway,
    ):
        self.user_repo = user_repo
        self.room_track_repo = room_track_repo
        self.room_repo = room_repo
        self.member_room_repo = member_room_repo

    async def get_room_player_state(
        self, room_id: uuid.UUID, current_user: UserEntity
    ) -> dict[str, str]:
        """
        Получает текущее состояние Spotify плеера для комнаты.
        """
        room = self.room_repo.get_room_by_id(room_id)
        if not room:
            logger.warning(f"RoomService: Комната с такпим id {room_id} не найдена")
            raise RoomNotFoundError()

        member_assoc = self.member_room_repo.get_member_room_association(
            room_id, current_user.id
        )
        if not member_assoc:
            raise UserNotInRoomError(
                detail="Вы не являетесь участником этой комнаты."
            )

        if not room.playback_host_id:
            logger.info(
                f"RoomService: Запрос состояния плеера для комнаты '{room_id}', но хост воспроизведения не назначен."
            )
            return {
                "is_playing": False,
                "current_track": None,
                "progress_ms": 0,
                "duration_ms": 0,
                "playback_host_id": None,
                "playback_host_username": None,
            }

        host_user = self.user_repo.get_user_by_id(room.playback_host_id)

        if not host_user:
            logger.error(
                f"RoomService: Хост воспроизведения '{room.playback_host_id}' для комнаты '{room_id}' не найден в БД при запросе состояния. Очищаем хоста."
            )
            await self.clear_playback_host(room_id)
            raise ServerError(
                status_code=500,
                detail="Внутренняя ошибка: Хост воспроизведения не найден.",
            )

        current_track_details: SpotifyTrackDetails | None = None
        current_track_assoc = None

        if room.current_playing_track_association_id:
            current_track_assoc = self.room_track_repo.get_association_by_id(
                room.current_playing_track_association_id
            )
            if current_track_assoc and current_track_assoc.track:
                current_track_details = SpotifyTrackDetails.model_validate(
                    current_track_assoc.track
                )

            logger.info(
                f"RoomService: Получено состояние плеера для комнаты '{room_id}'. Is playing: {room.is_playing}, Progress: {room.current_playback_progress_ms}ms."
            )

            return {
                "is_playing": room.is_playing,
                "current_track": (
                    current_track_details.model_dump()
                    if current_track_details
                    else None
                ),
                "progress_ms": room.current_track_position_ms,
                "duration_ms": (
                    current_track_assoc.track.duration_ms
                    if current_track_assoc and current_track_assoc.track
                    else 0
                ),
                "playback_host_id": str(room.playback_host_id),
                "playback_host_username": host_user.username,
            }