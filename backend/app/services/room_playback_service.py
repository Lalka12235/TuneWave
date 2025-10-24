import json
import uuid
from typing import Any

from fastapi import HTTPException, status

from app.exceptions.exception import (
    RoomNotFoundException,
    UnauthorizedRoomActionException,
)
from app.logger.log_config import logger
from app.models import User
from app.repositories.member_room_association_repo import (
    MemberRoomAssociationRepository,
)
from app.repositories.room_repo import RoomRepository
from app.repositories.room_track_association_repo import RoomTrackAssociationRepository
from app.repositories.user_repo import UserRepository

from app.schemas.enum import Role
from app.schemas.room_schemas import RoomResponse
from app.schemas.spotify_schemas import SpotifyTrackDetails

from app.services.mapper import RoomMapper
from app.services.spotify_service import SpotifyService

from app.ws.connection_manager import manager


class RoomService:

    def __init__(
            self,
            user_repo: UserRepository,
            room_track_repo: RoomTrackAssociationRepository,
            room_repo: RoomRepository,
            member_room_repo: MemberRoomAssociationRepository,
        ):
        self.user_repo = user_repo
        self.room_track_repo = room_track_repo
        self.room_repo = room_repo
        self.member_room_repo = member_room_repo

    
    async def set_playback_host(self, room_id: uuid.UUID, user_id: uuid.UUID,current_user: User) -> RoomResponse:
        """
        Назначает пользователя хостом воспроизведения для комнаты.
        Пользователь должен быть членом комнаты и иметь авторизацию Spotify с активным устройством.
        """
        room = self.room_repo.get_room_by_id(room_id)
        if not room:
            logger.warning(f'RoomService: Комната с такпим id {room_id} не найдена')
            raise RoomNotFoundException()
        current_user_assoc = self.member_room_repo.get_member_room_association(room_id,current_user.id)
        if not current_user_assoc:
            raise HTTPException(
                status_code=404,
                detail='Пользователь не найден в комнате'
            )
        if current_user_assoc.role not in [Role.MODERATOR,Role.OWNER]:
            logger.warning(f"API: Пользователь '{user_id}' попытался назначить хоста в комнате '{room_id}' без прав (роль: {current_user_assoc.role if current_user_assoc else 'None'}).")
            raise HTTPException(
                status_code=403,
                detail="Только владелец или модератор комнаты может назначить хоста воспроизведения."
            )
        
        member_assoc = self.member_room_repo.get_member_room_association(room_id,user_id)
        if not member_assoc:
            raise HTTPException(
                status_code=404,
                detail="Пользователь не является участником этой комнаты."
            )
        
        host_user = self.user_repo.get_user_by_id(user_id)
        if not host_user:
            raise HTTPException(status_code=404,detail="Указанный пользователь не найден.")
        
        if not host_user.spotify_access_token or not host_user.spotify_refresh_token:
            logger.warning(f"RoomService: Пользователь '{user_id}' не может быть хостом воспроизведения: не авторизован в Spotify.")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пользователь должен быть авторизован в Spotify, чтобы стать хостом воспроизведения."
             )
        
        spotify_service = SpotifyService(host_user)
        active_device_id = await spotify_service._get_device_id(host_user.spotify_access_token)
        if not active_device_id:
            logger.warning(f"RoomService: Пользователь '{user_id}' не может быть хостом воспроизведения: нет активных устройств Spotify.")
            raise HTTPException(
                status_code=400,
                detail="У пользователя нет активных устройств Spotify. Пожалуйста, запустите Spotify на одном из ваших устройств и повторите попытку."
            )
        
        room.playback_host_id = user_id
        room.active_spotify_device_id = active_device_id
        room.is_playing = False

        try:
            logger.info(f"RoomService: Пользователь '{user_id}' успешно назначен хостом воспроизведения для комнаты '{room_id}'.")
        except Exception as e:
            logger.error(f"RoomService: Ошибка при сохранении хоста воспроизведения для комнаты '{room_id}': {e}", exc_info=True)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Не удалось назначить хоста воспроизведения.")
        

        ws_message = {
            "action": "playback_host_changed",
            "room_id": str(room_id),
            "playback_host_id": str(room.playback_host_id),
            "playback_host_username": host_user.username,
            "active_spotify_device_id": room.active_spotify_device_id,
            "is_playing": room.is_playing,
            "message": f"'{host_user.username}' стал хостом воспроизведения."
        }
        await manager.broadcast(room_id, json.dumps(ws_message))
        logger.info(f"RoomService: Отправлено WS-уведомление о смене хоста воспроизведения в комнате '{room_id}'.")
        return RoomMapper.to_response(room)


    
    async def clear_playback_host(self, room_id: uuid.UUID) -> RoomResponse:
        """
        Очищает хоста воспроизведения для комнаты и сбрасывает состояние плеера.
        """
        room = self.room_repo.get_room_by_id(room_id)
        if not room.playback_host_id:
            logger.info(f"RoomService: Для комнаты '{room_id}' нет активного хоста воспроизведения для сброса.")
            return RoomMapper.to_response(room)
        
        old_host_id = room.playback_host_id

        
        try:
            room.playback_host_id = None
            room.active_spotify_device_id = None
            room.is_playing = False
            room.current_track_id = None
            room.current_track_position_ms = 0
            logger.info(f"RoomService: Хост воспроизведения для комнаты '{room_id}' (бывший хост: '{old_host_id}') успешно очищен.")
        except Exception as e:
            logger.error(f"RoomService: Ошибка при очистке хоста воспроизведения для комнаты '{room_id}': {e}", exc_info=True)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Не удалось очистить хоста воспроизведения.")
        
        ws_message = {
            "action": "playback_host_cleared",
            "room_id": str(room_id),
            "old_playback_host_id": str(old_host_id) if old_host_id else None,
            "message": "Хост воспроизведения комнаты был сброшен."
        }

        await manager.broadcast(room_id, json.dumps(ws_message))
        logger.info(f"RoomService: Отправлено WS-уведомление об очистке хоста воспроизведения в комнате '{room_id}'.")
        return RoomMapper.to_response(room)


    
    async def update_room_playback_state(
        self, 
        room_id: uuid.UUID, 
        current_playing_track_assoc_id: uuid.UUID | None, 
        progress_ms: int, 
        is_playing: bool
    ) -> RoomResponse:
        """
        Обновляет состояние воспроизведения в полях комнаты. 
        Используется, например, планировщиком или при получении состояния плеера от хоста.
        """
        room = self.room_repo.get_room_by_id(room_id)
        if not room:
            logger.warning(f'RoomService: Комната с такпим id {room_id} не найдена')
            raise RoomNotFoundException()

        room.current_playing_track_association_id = current_playing_track_assoc_id
        room.current_track_position_ms = progress_ms
        room.is_playing = is_playing


        try:
            logger.debug(f"RoomService: Обновлено состояние воспроизведения для комнаты '{room_id}'. Трек: '{current_playing_track_assoc_id}', Прогресс: {progress_ms}ms, Играет: {is_playing}.")
        except Exception as e:
            logger.error(f"RoomService: Ошибка при обновлении состояния воспроизведения для комнаты '{room_id}': {e}", exc_info=True)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Не удалось обновить состояние воспроизведения комнаты.")
        

        current_track_details: SpotifyTrackDetails | None = None
        current_track_assoc = None
        if current_playing_track_assoc_id:
            current_track_assoc = self.room_track_repo.get_association_by_id( current_playing_track_assoc_id)
            if current_track_assoc and current_track_assoc.track:
                current_track_details = SpotifyTrackDetails.model_validate(current_track_assoc.track)
        
        ws_message = {
            "action": "player_state_changed",
            "room_id": str(room_id),
            "is_playing": is_playing,
            "current_track_association_id": str(current_playing_track_assoc_id) if current_playing_track_assoc_id else None,
            "current_track": current_track_details.model_dump() if current_track_details else None,
            "progress_ms": progress_ms,
            "duration_ms": current_track_assoc.track.duration_ms if current_track_assoc and current_track_assoc.track else 0
        }
        await manager.broadcast(room_id, json.dumps(ws_message))
        logger.debug(f"RoomService: Отправлено WS-уведомление об изменении состояния плеера в комнате '{room_id}'.")
        return RoomMapper.to_response(room)

    
    async def player_command_play(
        self,
        room_id: uuid.UUID,
        current_user: User,
        track_uri: str| None = None,
        position_ms: int = 0
    ) -> dict[str, Any]:
        """
        Отправляет команду "PLAY" на Spotify плеер комнаты через хоста воспроизведения.
        """
        room = self.room_repo.get_room_by_id(room_id)
        if not room:
            logger.warning(f'RoomService: Комната с такпим id {room_id} не найдена')
            raise RoomNotFoundException()
        
        member_assoc = self.member_room_repo.get_member_room_association( room_id, current_user.id)
        if not member_assoc or member_assoc.role not in [Role.OWNER, Role.MODERATOR]:
            raise UnauthorizedRoomActionException(detail="Только владелец или модератор может управлять плеером.")
        
        if not room.playback_host_id or not room.active_spotify_device_id:
            logger.warning(f"RoomService: Попытка отправить команду 'play' в комнату '{room_id}', но нет активного хоста воспроизведения.")
            raise HTTPException(
                status_code=404,
                detail="В комнате нет активного хоста воспроизведения. Пожалуйста, назначьте хоста."
            )
        
        host_user = self.user_repo.get_user_by_id(room.playback_host_id)
        if not host_user:
            logger.error(f"RoomService: Хост воспроизведения '{room.playback_host_id}' для комнаты '{room_id}' не найден в БД. Очищаем хоста.")
            await self.clear_playback_host( room_id)
            raise HTTPException(
                status_code=500,
                detail="Внутренняя ошибка: Хост воспроизведения не найден."
            )
        
        spotify_service = SpotifyService( host_user)
        try:
            if track_uri:
                await spotify_service.play(
                    device_id=room.active_spotify_device_id,
                    track_uri=track_uri,
                    position_ms=position_ms
                )
                logger.info(f"RoomService: Хост '{host_user.id}' по команде пользователя '{current_user.id}' начал воспроизведение трека '{track_uri}' в комнате '{room_id}'.")
            else:
                await spotify_service.play(
                    device_id=room.active_spotify_device_id,
                    position_ms=position_ms
                )
                logger.info(f"RoomService: Хост '{host_user.id}' по команде пользователя '{current_user.id}' возобновил воспроизведение в комнате '{room_id}'.")
            
            room.is_playing = True

            playback_state = await spotify_service.get_playback_state()
            if playback_state:
                current_track_assoc_id: uuid.UUID | None = None
                if playback_state.get('current_track') and room.tracks_in_queue:
                    for assoc in room.tracks_in_queue:
                        if assoc.track and assoc.track.spotify_id == playback_state['current_track'].id:
                            current_track_assoc_id = assoc.id
                            break
                
                await self.update_room_playback_state(room_id,current_track_assoc_id, playback_state.get('progress_ms', 0), playback_state.get('is_playing', False))
        except HTTPException as e:
            logger.error(f"RoomService: Ошибка HTTP при команде 'play' в комнате '{room_id}' через хоста '{host_user.id}': {e.detail}", exc_info=True)
            raise e
        except Exception as e:
            logger.error(f"RoomService: Неизвестная ошибка при команде 'play' в комнате '{room_id}' через хоста '{host_user.id}': {e}", exc_info=True)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка при управлении плеером Spotify.")
        
        return {"message": "Команда 'play' успешно отправлена."}

    
    async def player_command_pause(
        self,
        room_id: uuid.UUID,
        current_user: User
    ) -> dict[str, Any]:
        """
        Отправляет команду "PAUSE" на Spotify плеер комнаты через хоста воспроизведения.
        """
        room = self.room_repo.get_room_by_id(room_id)
        if not room:
            logger.warning(f'RoomService: Комната с такпим id {room_id} не найдена')
            raise RoomNotFoundException()
        
        member_assoc = self.member_room_repo.get_member_room_association( room_id, current_user.id)
        if not member_assoc or member_assoc.role not in [Role.OWNER, Role.MODERATOR]:
            raise UnauthorizedRoomActionException(detail="Только владелец или модератор может управлять плеером.")
        
        if not room.playback_host_id or not room.active_spotify_device_id:
            logger.warning(f"RoomService: Попытка отправить команду 'pause' в комнату '{room_id}', но нет активного хоста воспроизведения.")
            raise HTTPException(
                status_code=404,
                detail="В комнате нет активного хоста воспроизведения. Пожалуйста, назначьте хоста."
            )
        
        host_user = self.user_repo.get_user_by_id(room.playback_host_id)
        if not host_user:
            logger.error(f"RoomService: Хост воспроизведения '{room.playback_host_id}' для комнаты '{room_id}' не найден в БД. Очищаем хоста.")
            await self.clear_playback_host( room_id)
            raise HTTPException(
                status_code=500,
                detail="Внутренняя ошибка: Хост воспроизведения не найден."
            )
        
        spotify_service = SpotifyService( host_user)
        try:
            await spotify_service.pause(
                device_id=room.active_spotify_device_id,
            )
            logger.info(f"RoomService: Хост '{host_user.id}' по команде пользователя '{current_user.id}' остановил воспроизведение трека '{room.current_track_id}' в комнате '{room_id}'.")
            room.is_playing = False

            playback_state = await spotify_service.get_playback_state()
            if playback_state:
                current_track_assoc_id: uuid.UUID | None = None
                if playback_state.get('current_track') and room.tracks_in_queue:
                    for assoc in room.tracks_in_queue:
                        if assoc.track and assoc.track.spotify_id == playback_state['current_track'].id:
                            current_track_assoc_id = assoc.id
                            break
                
                await self.update_room_playback_state(room_id,current_track_assoc_id, playback_state.get('progress_ms', 0), playback_state.get('is_playing', False))
        except HTTPException as e:
            logger.error(f"RoomService: Ошибка HTTP при команде 'pause' в комнате '{room_id}' через хоста '{host_user.id}': {e.detail}", exc_info=True)
            raise e
        except Exception as e:
            logger.error(f"RoomService: Неизвестная ошибка при команде 'pause' в комнате '{room_id}' через хоста '{host_user.id}': {e}", exc_info=True)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка при управлении плеером Spotify.")
        
        return {"message": "Команда 'pause' успешно отправлена."}

    
    async def player_command_skip_next(
        self,
        room_id: uuid.UUID,
        current_user: User
    ) -> dict[str, Any]:    
        """
        Отправляет команду "SKIP NEXT" на Spotify плеер комнаты через хоста воспроизведения.
        """
        room = self.room_repo.get_room_by_id(room_id)
        if not room:
            logger.warning(f'RoomService: Комната с такпим id {room_id} не найдена')
            raise RoomNotFoundException()
        
        member_assoc = self.member_room_repo.get_member_room_association( room_id, current_user.id)
        if not member_assoc or member_assoc.role not in [Role.OWNER, Role.MODERATOR]:
            raise UnauthorizedRoomActionException(detail="Только владелец или модератор может управлять плеером.")
        
        if not room.playback_host_id or not room.active_spotify_device_id:
            logger.warning(f"RoomService: Попытка отправить команду 'skip next' в комнату '{room_id}', но нет активного хоста воспроизведения.")
            raise HTTPException(
                status_code=404,
                detail="В комнате нет активного хоста воспроизведения. Пожалуйста, назначьте хоста."
            )
        
        host_user = self.user_repo.get_user_by_id(room.playback_host_id)
        if not host_user:
            logger.error(f"RoomService: Хост воспроизведения '{room.playback_host_id}' для комнаты '{room_id}' не найден в БД. Очищаем хоста.")
            await self.clear_playback_host( room_id)
            raise HTTPException(
                status_code=500,
                detail="Внутренняя ошибка: Хост воспроизведения не найден."
            )
        
        spotify_service = SpotifyService( host_user)
        try:
            await spotify_service.skip_next(
                device_id=room.active_spotify_device_id
            )
            logger.info(f"RoomService: Хост '{host_user.id}' по команде пользователя '{current_user.id}' переключил на следующий трек в комнате '{room_id}'.")

            playback_state = await spotify_service.get_playback_state()
            if playback_state:
                current_track_assoc_id: uuid.UUID | None = None
                if playback_state.get('current_track') and room.tracks_in_queue:
                    for assoc in room.tracks_in_queue:
                        if assoc.track and assoc.track.spotify_id == playback_state['current_track'].id:
                            current_track_assoc_id = assoc.id
                            break
                
                await self.update_room_playback_state(room_id,current_track_assoc_id, playback_state.get('progress_ms', 0), playback_state.get('is_playing', False))
        except HTTPException as e:
            logger.error(f"RoomService: Ошибка HTTP при команде 'skip next' в комнате '{room_id}' через хоста '{host_user.id}': {e.detail}", exc_info=True)
            raise e
        except Exception as e:
            logger.error(f"RoomService: Неизвестная ошибка при команде 'skip next' в комнате '{room_id}' через хоста '{host_user.id}': {e}", exc_info=True)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка при управлении плеером Spotify.")
        
        return {"message": "Команда 'skip next' успешно отправлена."}

    
    async def player_command_skip_previous(
        self,
        room_id: uuid.UUID,
        current_user: User
    ) -> dict[str, Any]:
        """
        Отправляет команду "SKIP PREVIOUS" на Spotify плеер комнаты через хоста воспроизведения.
        """
        room = self.room_repo.get_room_by_id(room_id)
        if not room:
            logger.warning(f'RoomService: Комната с такпим id {room_id} не найдена')
            raise RoomNotFoundException()
        
        member_assoc = self.member_room_repo.get_member_room_association( room_id, current_user.id)
        if not member_assoc or member_assoc.role not in [Role.OWNER, Role.MODERATOR]:
            raise UnauthorizedRoomActionException(detail="Только владелец или модератор может управлять плеером.")
        
        if not room.playback_host_id or not room.active_spotify_device_id:
            logger.warning(f"RoomService: Попытка отправить команду 'skip previous' в комнату '{room_id}', но нет активного хоста воспроизведения.")
            raise HTTPException(
                status_code=404,
                detail="В комнате нет активного хоста воспроизведения. Пожалуйста, назначьте хоста."
            )
        
        host_user = self.user_repo.get_user_by_id(room.playback_host_id)
        if not host_user:
            logger.error(f"RoomService: Хост воспроизведения '{room.playback_host_id}' для комнаты '{room_id}' не найден в БД. Очищаем хоста.")
            await self.clear_playback_host( room_id)
            raise HTTPException(
                status_code=500,
                detail="Внутренняя ошибка: Хост воспроизведения не найден."
            )
        
        spotify_service = SpotifyService( host_user)
        try:
            await spotify_service.skip_next(
                device_id=room.active_spotify_device_id
            )
            logger.info(f"RoomService: Хост '{host_user.id}' по команде пользователя '{current_user.id}' переключил на предыдущий трек в комнате '{room_id}'.")

            playback_state = await spotify_service.get_playback_state()
            if playback_state:
                current_track_assoc_id: uuid.UUID | None = None
                if playback_state.get('current_track') and room.tracks_in_queue:
                    for assoc in room.tracks_in_queue:
                        if assoc.track and assoc.track.spotify_id == playback_state['current_track'].id:
                            current_track_assoc_id = assoc.id
                            break
                
                await self.update_room_playback_state(room_id,current_track_assoc_id, playback_state.get('progress_ms', 0), playback_state.get('is_playing', False))
        except HTTPException as e:
            logger.error(f"RoomService: Ошибка HTTP при команде 'skip previous' в комнате '{room_id}' через хоста '{host_user.id}': {e.detail}", exc_info=True)
            raise e
        except Exception as e:
            logger.error(f"RoomService: Неизвестная ошибка при команде 'skip previous' в комнате '{room_id}' через хоста '{host_user.id}': {e}", exc_info=True)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка при управлении плеером Spotify.")
        
        return {"message": "Команда 'skip previous' успешно отправлена."}


    
    async def get_room_player_state(
        self, 
        room_id: uuid.UUID, 
        current_user: User
    ) -> dict[str, Any]:
        """
        Получает текущее состояние Spotify плеера для комнаты.
        """
        room = self.room_repo.get_room_by_id(room_id)
        if not room:
            logger.warning(f'RoomService: Комната с такпим id {room_id} не найдена')
            raise RoomNotFoundException()

        member_assoc = self.member_room_repo.get_member_room_association( room_id, current_user.id)
        if not member_assoc:
            raise UnauthorizedRoomActionException(detail="Вы не являетесь участником этой комнаты.")
        
        if not room.playback_host_id:
            logger.info(f"RoomService: Запрос состояния плеера для комнаты '{room_id}', но хост воспроизведения не назначен.")
            return {
                'is_playing': False,
                'current_track': None,
                'progress_ms': 0,
                'duration_ms': 0,
                'playback_host_id': None,
                'playback_host_username': None
            }
        
        host_user = self.user_repo.get_user_by_id( room.playback_host_id)

        if not host_user:
            logger.error(f"RoomService: Хост воспроизведения '{room.playback_host_id}' для комнаты '{room_id}' не найден в БД при запросе состояния. Очищаем хоста.")
            await self.clear_playback_host(room_id)
            raise HTTPException(
                status_code=500,
                detail="Внутренняя ошибка: Хост воспроизведения не найден."
            )
        
        current_track_details: SpotifyTrackDetails | None = None
        current_track_assoc = None

        if room.current_playing_track_association_id:
            current_track_assoc = self.room_track_repo.get_association_by_id( room.current_playing_track_association_id)
            if current_track_assoc and current_track_assoc.track:
                current_track_details = SpotifyTrackDetails.model_validate(current_track_assoc.track)
        
            logger.info(f"RoomService: Получено состояние плеера для комнаты '{room_id}'. Is playing: {room.is_playing}, Progress: {room.current_playback_progress_ms}ms.")

            return {
                "is_playing": room.is_playing,
                "current_track": current_track_details.model_dump() if current_track_details else None,
                "progress_ms": room.current_track_position_ms,
                "duration_ms": current_track_assoc.track.duration_ms if current_track_assoc and current_track_assoc.track else 0,
                "playback_host_id": str(room.playback_host_id),
                "playback_host_username": host_user.username
            }