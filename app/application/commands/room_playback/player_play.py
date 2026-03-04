import uuid

from app.config.log_config import logger
from app.domain.entity.user import UserEntity
from app.domain.interfaces.member_room_association import MemberRoomAssociationGateway
from app.domain.interfaces.room_gateway import RoomGateway
from app.domain.interfaces.user_gateway import UserGateway

from app.domain.enum import Role

from app.infrastructure.external.spotify import SpotifyService


from app.domain.exceptions.exception import ServerError
from app.domain.exceptions.room_exception import (
    RoomNotFoundError,
    RoomPermissionDeniedError,
    RoomHostNotFoundError,
)


class PlayerPlay:
    def __init__(
        self,
        user_repo: UserGateway,
        room_repo: RoomGateway,
        member_room_repo: MemberRoomAssociationGateway,
    ):
        self.user_repo = user_repo
        self.room_repo = room_repo
        self.member_room_repo = member_room_repo

    async def player_command_play(
        self,
        room_id: uuid.UUID,
        current_user: UserEntity,
        track_uri: str | None = None,
        position_ms: int = 0,
    ) -> dict[str, str]:
        """
        Отправляет команду "PLAY" на Spotify плеер комнаты через хоста воспроизведения.
        """
        room = self.room_repo.get_room_by_id(room_id)
        if not room:
            logger.warning(f"RoomService: Комната с такпим id {room_id} не найдена")
            raise RoomNotFoundError()

        member_assoc = self.member_room_repo.get_member_room_association(
            room_id, current_user.id
        )
        if not member_assoc or member_assoc.role not in [Role.OWNER, Role.MODERATOR]:
            raise RoomPermissionDeniedError(
                detail="Только владелец или модератор может управлять плеером."
            )

        if not room.playback_host_id or not room.active_spotify_device_id:
            logger.warning(
                f"RoomService: Попытка отправить команду 'play' в комнату '{room_id}', но нет активного хоста воспроизведения."
            )
            raise RoomHostNotFoundError()

        host_user = self.user_repo.get_user_by_id(room.playback_host_id)
        if not host_user:
            logger.error(
                f"RoomService: Хост воспроизведения '{room.playback_host_id}' для комнаты '{room_id}' не найден в БД. Очищаем хоста."
            )
            await self.clear_playback_host(room_id)
            raise ServerError(
                detail="Внутренняя ошибка: Хост воспроизведения не найден.",
            )

        spotify_service = SpotifyService(host_user)
        try:
            if track_uri:
                await spotify_service.play(
                    device_id=room.active_spotify_device_id,
                    track_uri=track_uri,
                    position_ms=position_ms,
                )
                logger.info(
                    f"RoomService: Хост '{host_user.id}' по команде пользователя '{current_user.id}' начал воспроизведение трека '{track_uri}' в комнате '{room_id}'."
                )
            else:
                await spotify_service.play(
                    device_id=room.active_spotify_device_id, position_ms=position_ms
                )
                logger.info(
                    f"RoomService: Хост '{host_user.id}' по команде пользователя '{current_user.id}' возобновил воспроизведение в комнате '{room_id}'."
                )

            room.is_playing = True

            playback_state = await spotify_service.get_playback_state()
            if playback_state:
                current_track_assoc_id: uuid.UUID | None = None
                if playback_state.get("current_track") and room.tracks_in_queue:
                    for assoc in room.tracks_in_queue:
                        if (
                            assoc.track
                            and assoc.track.spotify_id
                            == playback_state["current_track"].id
                        ):
                            current_track_assoc_id = assoc.id
                            break

                await self.update_room_playback_state(
                    room_id,
                    current_track_assoc_id,
                    playback_state.get("progress_ms", 0),
                    playback_state.get("is_playing", False),
                )
        except Exception as e:
            logger.error(
                f"RoomService: Неизвестная ошибка при команде 'play' в комнате '{room_id}' через хоста '{host_user.id}': {e}",
                exc_info=True,
            )
            raise ServerError(
                detail="Ошибка при управлении плеером Spotify.",
            )

        return {"message": "Команда 'play' успешно отправлена."}