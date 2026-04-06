import uuid

from app.config.log_config import logger
from app.domain.entity.user import UserEntity
from app.domain.interfaces.member_room_association import MemberRoomAssociationGateway
from app.domain.interfaces.room_gateway import RoomGateway
from app.domain.interfaces.user_gateway import UserGateway

from app.domain.enum import Role
from app.presentation.schemas.room_schemas import RoomResponse

from app.infrastructure.external.spotify import SpotifyService

from app.infrastructure.ws.manager_notify_service import NotifyService

from app.domain.exceptions.exception import ServerError
from app.domain.exceptions.room_exception import (
    UserNotInRoomError,
    RoomNotFoundError,
    RoomPermissionDeniedError,
)
from app.infrastructure.external.exception.spotify_exception import SpotifyAuthorizeError,SpotifyDeviceNotFoundError


class SetPlaybackHost:
    def __init__(
        self,
        user_repo: UserGateway,
        room_repo: RoomGateway,
        member_room_repo: MemberRoomAssociationGateway,
        notify_service: NotifyService,
    ):
        self.user_repo = user_repo
        self.room_repo = room_repo
        self.member_room_repo = member_room_repo
        self.notify_service = notify_service

    async def set_playback_host(
        self, room_id: uuid.UUID, user_id: uuid.UUID, current_user: UserEntity
    ) -> RoomResponse:
        """
        Назначает пользователя хостом воспроизведения для комнаты.
        Пользователь должен быть членом комнаты и иметь авторизацию Spotify с активным устройством.
        """
        room = self.room_repo.get_room_by_id(room_id)
        if not room:
            logger.warning(f"RoomService: Комната с такпим id {room_id} не найдена")
            raise RoomNotFoundError()
        current_user_assoc = self.member_room_repo.get_member_room_association(
            room_id, current_user.id
        )
        if not current_user_assoc:
            raise UserNotInRoomError()
        if current_user_assoc.role not in [Role.MODERATOR, Role.OWNER]:
            logger.warning(
                f"API: Пользователь '{user_id}' попытался назначить хоста в комнате '{room_id}' без прав (роль: {current_user_assoc.role if current_user_assoc else 'None'})."
            )
            raise RoomPermissionDeniedError(
                detail="Только владелец или модератор комнаты может назначить хоста воспроизведения."
            )

        member_assoc = self.member_room_repo.get_member_room_association(
            room_id, user_id
        )
        if not member_assoc:
            raise UserNotInRoomError(
                detail="Пользователь не является участником этой комнаты."
            )

        host_user = self.user_repo.get_user_by_id(user_id)
        if not host_user:
            raise UserNotInRoomError(detail="Указанный пользователь не найден.")

        if not host_user.spotify_access_token or not host_user.spotify_refresh_token:
            logger.warning(
                f"RoomService: Пользователь '{user_id}' не может быть хостом воспроизведения: не авторизован в Spotify."
            )
            raise SpotifyAuthorizeError(
                detail="Пользователь должен быть авторизован в Spotify, чтобы стать хостом воспроизведения."
            )

        spotify_service = SpotifyService(host_user)
        active_device_id = await spotify_service._get_device_id(
            host_user.spotify_access_token
        )
        if not active_device_id:
            logger.warning(
                f"RoomService: Пользователь '{user_id}' не может быть хостом воспроизведения: нет активных устройств Spotify."
            )
            raise SpotifyDeviceNotFoundError(
                status_code=400,
                detail="У пользователя нет активных устройств Spotify. Пожалуйста, запустите Spotify на одном из ваших устройств и повторите попытку.",
            )

        room.playback_host_id = user_id
        room.active_spotify_device_id = active_device_id
        room.is_playing = False

        try:
            logger.info(
                f"RoomService: Пользователь '{user_id}' успешно назначен хостом воспроизведения для комнаты '{room_id}'."
            )
        except Exception as e:
            logger.error(
                f"RoomService: Ошибка при сохранении хоста воспроизведения для комнаты '{room_id}': {e}",
                exc_info=True,
            )
            raise ServerError(detail="Не удалось назначить хоста воспроизведения.")

        await self.notify_service.send_mesasge_for_user(
            {
            "action": "playback_host_changed",
            "room_id": str(room_id),
            "playback_host_id": str(room.playback_host_id),
            "playback_host_username": host_user.username,
            "active_spotify_device_id": room.active_spotify_device_id,
            "is_playing": room.is_playing,
            "message": f"'{host_user.username}' стал хостом воспроизведения.",
            }
        )
        logger.info(
            f"RoomService: Отправлено WS-уведомление о смене хоста воспроизведения в комнате '{room_id}'."
        )
        return room