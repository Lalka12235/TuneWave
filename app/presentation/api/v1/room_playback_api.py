import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Body,status

from app.domain.entity import UserEntity

from dishka.integrations.fastapi import DishkaRoute,FromDishka
from app.application.commands.room_playback import ReadPlayerState,UpdateRoomPlaybackState,PlayerPause,PlayerPlay,PlayerPrevious,PlayerSkip,SetPlaybackHost,ClearPlaybackState

room_playback = APIRouter(tags=["Room"], prefix="/rooms",route_class=DishkaRoute)

user_dependencies = FromDishka[UserEntity]

@room_playback.put(
    "/{room_id}/playback-host",
    status_code=status.HTTP_200_OK,
    response_model=dict[str, Any],
)
async def set_room_playback_host(
    room_id: uuid.UUID,
    interactor: FromDishka[SetPlaybackHost],
    user_id_to_set_as_host: Annotated[uuid.UUID, Body(..., embed=True)],
    current_user: user_dependencies,
) -> dict[str, Any]:
    """
    Назначает указанного пользователя хостом воспроизведения для комнаты.
    Только владелец или модератор могут назначить хоста.
    Назначаемый пользователь должен быть авторизован в Spotify и иметь активное устройство.
    """
    return await interactor.set_playback_host(
        room_id, user_id_to_set_as_host,current_user
    )


@room_playback.put("/{room_id}/player/play", status_code=status.HTTP_204_NO_CONTENT)
async def player_play_command(
    room_id: uuid.UUID,
    current_user: user_dependencies,
     interactor: FromDishka[PlayerPlay],
    track_uri: str | None = None,
    position_ms: int = 0,
):
    """
    Запускает или возобновляет воспроизведение Spotify в комнате через хоста воспроизведения.
    """
    return await interactor.player_command_play(
        room_id, current_user, track_uri=track_uri, position_ms=position_ms
    )


@room_playback.put("/{room_id}/player/pause", status_code=status.HTTP_204_NO_CONTENT)
async def player_pause_command(
    room_id: uuid.UUID,
    current_user: user_dependencies,
     interactor: FromDishka[PlayerPause],
):
    """
    Ставит воспроизведение Spotify на паузу в комнате через хоста воспроизведения.
    """
    return await interactor.player_command_pause(room_id, current_user)


@room_playback.post("/{room_id}/player/next", status_code=status.HTTP_204_NO_CONTENT)
async def player_skip_next_command(
    room_id: uuid.UUID,
    current_user: user_dependencies,
     interactor: FromDishka[PlayerSkip],
):
    """
    Переключает на следующий трек в Spotify плеере комнаты через хоста воспроизведения.
    """
    return await interactor.player_command_skip_next(room_id, current_user)


@room_playback.post(
    "/{room_id}/player/previous", status_code=status.HTTP_204_NO_CONTENT
)
async def player_skip_previous_command(
    room_id: uuid.UUID,
    current_user: user_dependencies,
    interactor: FromDishka[PlayerPrevious],
):
    """
    Переключает на предыдущий трек в Spotify плеере комнаты через хоста воспроизведения.
    """
    return await interactor.player_command_skip_previous(
        room_id, current_user
    )


@room_playback.get("/{room_id}/player/state", response_model=dict[str, Any])
async def get_room_player_state(
    room_id: uuid.UUID,
    current_user: user_dependencies,
     interactor: FromDishka[ReadPlayerState],
) -> dict[str, Any]:
    """
    Получает текущее состояние Spotify плеера для комнаты.
    """
    return await interactor.get_room_player_state(room_id, current_user)