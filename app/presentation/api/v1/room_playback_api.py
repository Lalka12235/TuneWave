import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Body,status

from app.domain.entity import UserEntity
from app.application.services.room_playback_service import RoomPlaybackService

from dishka import FromDishka

room_playback = APIRouter(tags=["Room"], prefix="/rooms")

user_dependencies = FromDishka[UserEntity]
room_playback_service = FromDishka[RoomPlaybackService]



@room_playback.put(
    "/{room_id}/playback-host",
    status_code=status.HTTP_200_OK,
    response_model=dict[str, Any],
)
async def set_room_playback_host(
    room_id: uuid.UUID,
    room_playback_service: room_playback_service,
    user_id_to_set_as_host: Annotated[uuid.UUID, Body(..., embed=True)],
    current_user: user_dependencies,
) -> dict[str, Any]:
    """
    Назначает указанного пользователя хостом воспроизведения для комнаты.
    Только владелец или модератор могут назначить хоста.
    Назначаемый пользователь должен быть авторизован в Spotify и иметь активное устройство.
    """
    return await room_playback_service.set_playback_host(
        room_id, user_id_to_set_as_host
    )


@room_playback.put("/{room_id}/player/play", status_code=status.HTTP_204_NO_CONTENT)
async def player_play_command(
    room_id: uuid.UUID,
    current_user: user_dependencies,
    room_playback_service: room_playback_service,
    track_uri: str | None = None,
    position_ms: int = 0,
):
    """
    Запускает или возобновляет воспроизведение Spotify в комнате через хоста воспроизведения.
    """
    return await room_playback_service.player_command_play(
        room_id, current_user, track_uri=track_uri, position_ms=position_ms
    )


@room_playback.put("/{room_id}/player/pause", status_code=status.HTTP_204_NO_CONTENT)
async def player_pause_command(
    room_id: uuid.UUID,
    current_user: user_dependencies,
    room_playback_service: room_playback_service,
):
    """
    Ставит воспроизведение Spotify на паузу в комнате через хоста воспроизведения.
    """
    return await room_playback_service.player_command_pause(room_id, current_user)


@room_playback.post("/{room_id}/player/next", status_code=status.HTTP_204_NO_CONTENT)
async def player_skip_next_command(
    room_id: uuid.UUID,
    current_user: user_dependencies,
    room_playback_service: room_playback_service,
):
    """
    Переключает на следующий трек в Spotify плеере комнаты через хоста воспроизведения.
    """
    return await room_playback_service.player_command_skip_next(room_id, current_user)


@room_playback.post(
    "/{room_id}/player/previous", status_code=status.HTTP_204_NO_CONTENT
)
async def player_skip_previous_command(
    room_id: uuid.UUID,
    current_user: user_dependencies,
    room_playback_service: room_playback_service,
):
    """
    Переключает на предыдущий трек в Spotify плеере комнаты через хоста воспроизведения.
    """
    return await room_playback_service.player_command_skip_previous(
        room_id, current_user
    )


@room_playback.get("/{room_id}/player/state", response_model=dict[str, Any])
async def get_room_player_state(
    room_id: uuid.UUID,
    current_user: user_dependencies,
    room_playback_service: room_playback_service,
) -> dict[str, Any]:
    """
    Получает текущее состояние Spotify плеера для комнаты.
    """
    return await room_playback_service.get_room_player_state(room_id, current_user)
