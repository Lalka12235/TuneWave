import json
import uuid
from typing import Annotated, Any, Callable

from fastapi import APIRouter, Body, Depends, Path, Query, status
from fastapi_limiter.depends import RateLimiter
from infrastructure.redis.redis import get_redis_client
from redis.asyncio import Redis

from app.auth.auth import get_current_user
from app.logger.log_config import logger
from app.models.user import User
from app.schemas.ban_schemas import BanCreate, BanResponse
from app.schemas.room_member_schemas import (
    JoinRoomRequest,
    RoomMemberResponse,
    RoomMemberRoleUpdate,
)
from app.schemas.room_schemas import (
    AddTrackToQueueRequest,
    InviteResponse,
    RoomCreate,
    RoomResponse,
    RoomUpdate,
    TrackInQueueResponse,
)
from app.schemas.user_schemas import UserResponse
from app.services.room_service import RoomService
from app.services.dep import get_room_service

room = APIRouter(tags=["Room"], prefix="/rooms")

user_dependencies = Annotated[User, Depends(get_current_user)]


def cache(key_generator: Callable, expiration: int = 300):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Извлекаем redis_client из kwargs (он будет добавлен FastAPI)
            redis_client: Redis = kwargs.get("redis_client")

            # Если Redis недоступен, выполняем функцию без кэширования
            if not redis_client:
                logger.warning("Redis client not available, skipping cache...")
                return await func(*args, **kwargs)

            # ✅ Используем переданную функцию-генератор для создания ключа
            try:
                cache_key = key_generator(*args, **kwargs)
            except Exception as e:
                logger.error(
                    f"Error generating cache key: {e}. Skipping cache...", exc_info=True
                )
                return await func(*args, **kwargs)

            # 1. Пробуем получить данные из кэша
            cached_data = await redis_client.get(cache_key)
            if cached_data:
                logger.info(f"Cache hit for key: {cache_key}")
                return json.loads(cached_data)

            # 2. Если данных в кэше нет, выполняем оригинальную функцию
            logger.info(f"Cache miss for key: {cache_key}. Fetching from DB...")
            result = await func(*args, **kwargs)

            await redis_client.setex(cache_key, expiration, json.dumps(result))
            return result

        return wrapper

    return decorator


@room.post(
    "/",
    response_model=RoomResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RateLimiter(times=5, seconds=60))],
)
async def create_room(
    room_data: RoomCreate,
    current_user: user_dependencies,
    room_service: Annotated[RoomService,Depends(get_room_service)],
) -> RoomResponse:
    """
    Создает новую комнату.
    Требуется аутентификация. Владелец комнаты будет текущим аутентифицированным пользователем.
    """
    return await room_service.create_room(room_data, current_user)


@room.put(
    "/{room_id}",
    response_model=RoomResponse,
    dependencies=[Depends(RateLimiter(times=10, seconds=60))],
)
def update_room(
    room_id: Annotated[uuid.UUID, Path(..., description="ID комнаты для обновления")],
    update_data: RoomUpdate,
    current_user: user_dependencies,
    room_service: Annotated[RoomService,Depends(get_room_service)],
) -> RoomResponse:
    """
    Обновляет информацию о комнате по ее ID.
    Требуется аутентификация. Только владелец комнаты может ее обновить.
    """
    return room_service.update_room(room_id, update_data, current_user)


@room.delete(
    "/{room_id}",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(RateLimiter(times=10, seconds=60))],
)
def delete_room(
    room_id: Annotated[uuid.UUID, Path(..., description="ID комнаты для удаления")],
    current_user: user_dependencies,
    room_service: Annotated[RoomService,Depends(get_room_service)],
) -> dict:
    """
    Удаляет комнату по ее ID.
    Требуется аутентификация. Только владелец комнаты может ее удалить.
    """
    return room_service.delete_room(room_id, current_user)


@room.post(
    "/{room_id}/join",
    response_model=RoomResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(RateLimiter(times=10, seconds=60))],
)
async def join_room(
    room_id: Annotated[
        uuid.UUID,
        Path(..., description="ID комнаты, к которой присоединяется пользователь"),
    ],
    current_user: user_dependencies,
    request_data: JoinRoomRequest,
    room_service: Annotated[RoomService,Depends(get_room_service)],
) -> RoomResponse:
    """
    Пользователь присоединяется к комнате.
    Требуется аутентификация. Если комната приватная, требуется пароль.
    """
    return await room_service.join_room(current_user, room_id, request_data.password)


@room.post("/{room_id}/leave", status_code=status.HTTP_200_OK)
async def leave_room(
    room_id: Annotated[
        uuid.UUID, Path(..., description="ID комнаты, которую покидает пользователь")
    ],
    current_user: user_dependencies,
    room_service: Annotated[RoomService,Depends(get_room_service)],
) -> dict:
    """
    Пользователь покидает комнату.
    Требуется аутентификация.
    """
    return await room_service.leave_room(room_id, current_user)


@room.get(
    "/{room_id}/members",
    response_model=list[UserResponse],
    dependencies=[Depends(RateLimiter(times=10, seconds=60))],
)
@cache(
    key_generator=lambda room_id, **kwargs: f"room_members:{room_id}", expiration=300
)
async def get_room_members(
    room_id: Annotated[
        uuid.UUID, Path(..., description="ID комнаты для получения списка участников")
    ],
    room_service: Annotated[RoomService,Depends(get_room_service)],
    redis_client: Annotated[Redis,Depends(get_redis_client)],
    
) -> list[UserResponse]:
    """
    Получает список всех участников комнаты.
    Не требует аутентификации.
    """
    return await room_service.get_room_members(room_id)


@room.get(
    "/by-name/",
    response_model=RoomResponse,
    dependencies=[Depends(RateLimiter(times=10, seconds=60))],
)
@cache(key_generator=lambda name, **kwargs: f"room_name:{name}", expiration=300)
async def get_room_by_name(
    name: Annotated[str, Query(..., description="Название комнаты")],
    room_service: Annotated[RoomService,Depends(get_room_service)],
    redis_client: Annotated[Redis,Depends(get_redis_client)],
) -> RoomResponse:
    """
    Получает информацию о комнате по ее названию.
    Не требует аутентификации.
    """
    return await room_service.get_room_by_name(name)


@room.get(
    "/my-rooms",
    response_model=list[RoomResponse],
    dependencies=[Depends(RateLimiter(times=10, seconds=60))],
)
@cache(
    key_generator=lambda current_user, **kwargs: f"room_my:{current_user.id}",
    expiration=300,
)
async def get_my_rooms(
    current_user: user_dependencies,room_service: Annotated[RoomService,Depends(get_room_service)], redis_client: Redis = Depends(get_redis_client)
) -> list[RoomResponse]:
    """
    Получает список всех комнат, в которых состоит текущий аутентифицированный пользователь.
    Требуется аутентификация.
    """
    return await room_service.get_user_rooms(current_user)


@room.get(
    "/",
    response_model=list[RoomResponse],
    dependencies=[Depends(RateLimiter(times=10, seconds=60))],
)
async def get_all_rooms(
    room_service: Annotated[RoomService,Depends(get_room_service)],
    redis_client: Annotated[Redis,Depends(get_redis_client)],
) -> list[RoomResponse]:
    """
    Получает список всех доступных комнат.
    Не требует аутентификации.
    """
    return await room_service.get_all_rooms()


@room.get(
    "/{room_id}",
    response_model=RoomResponse,
    dependencies=[Depends(RateLimiter(times=10, seconds=60))],
)
@cache(key_generator=lambda room_id, **kwargs: f"room_id:{room_id}", expiration=300)
async def get_room_by_id(
    room_id: Annotated[uuid.UUID, Path(..., description="Уникальный ID комнаты")],
    room_service: Annotated[RoomService,Depends(get_room_service)],
    redis_client: Annotated[Redis,Depends(get_redis_client)],
) -> RoomResponse:
    """
    Получает информацию о комнате по ее ID.
    Не требует аутентификации.
    """
    return await room_service.get_room_by_id(room_id)


@room.post(
    "/{room_id}/queue",
    response_model=TrackInQueueResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RateLimiter(times=10, seconds=60))],
)
async def add_track_to_queue(
    current_user: user_dependencies,
    request: AddTrackToQueueRequest,
    room_id: Annotated[uuid.UUID, Path(..., description="Уникальный ID комнаты")],
    room_service: Annotated[RoomService,Depends(get_room_service)],
) -> TrackInQueueResponse:
    """
    Добавляет трек в очередь комнаты. Только владелец комнаты может это сделать.
    """
    association = await room_service.add_track_to_queue(
        room_id=room_id, track_spotify_id=request.spotify_id, current_user=current_user
    )
    return association


@room.get(
    "/{room_id}/queue/{association_id}",
    response_model=list[TrackInQueueResponse],
    dependencies=[Depends(RateLimiter(times=10, seconds=60))],
)
async def get_room_queue(
    room_id: Annotated[uuid.UUID, Path(..., description="Уникальный ID комнаты")],
    room_service: Annotated[RoomService,Depends(get_room_service)],
    redis_client: Annotated[Redis,Depends(get_redis_client)],
) -> list[TrackInQueueResponse]:
    """
    Получает текущую очередь треков для комнаты.
    """
    return room_service.get_room_queue(room_id)


@room.delete(
    "/{room_id}/queue/{association_id}",
    dependencies=[Depends(RateLimiter(times=10, seconds=60))],
)
async def remove_track_from_queue(
    current_user: user_dependencies,
    room_id: Annotated[uuid.UUID, Path(..., description="Уникальный ID комнаты")],
    association_id: Annotated[
        uuid.UUID, Path(..., description="ID ассоциации трека в очереди")
    ],
    room_service: Annotated[RoomService,Depends(get_room_service)],
) -> dict:
    """
    Удаляет трек из очереди комнаты по ID ассоциации. Только владелец комнаты может это сделать.
    """
    return await room_service.remove_track_from_queue(
        room_id, association_id, current_user.id
    )


@room.put(
    "/{room_id}/members/{target_user_id}/role",
    response_model=RoomMemberResponse,
    dependencies=[Depends(RateLimiter(times=5, seconds=60))],
)
async def update_member_role(
    room_id: Annotated[
        uuid.UUID,
        Path(..., description="ID комнаты, к которой присоединяется пользователь"),
    ],
    target_user_id: Annotated[
        uuid.UUID, Path(..., description="ID пользователя, чью роль нужно изменить")
    ],
    user: user_dependencies,
    new_role: RoomMemberRoleUpdate,
    room_service: Annotated[RoomService,Depends(get_room_service)],
) -> RoomMemberResponse:
    """
    Изменяет роль члена комнаты. Доступно только владельцу комнаты.

    Args:
        room_id (uuid.UUID): Уникальный ID комнаты.
        target_user_id (uuid.UUID): Уникальный ID пользователя, чью роль нужно изменить.
        new_role_data (RoomMemberRoleUpdate): Pydantic-модель, содержащая новую роль ('member', 'moderator', 'owner').
        db (Session): Сессия базы данных.
        current_user (User): Текущий аутентифицированный пользователь, который пытается изменить роль.

    Returns:
        RoomMemberResponse: Обновленная информация о члене комнаты с новой ролью.

    Raises:
        HTTPException: Если комната не найдена, у пользователя нет прав, или произошла ошибка.
    """
    return await room_service.update_member_role(
        room_id, target_user_id, new_role.role, user
    )


@room.post(
    "/{room_id}/members/{user_id}/ban",
    response_model=BanResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RateLimiter(times=5, seconds=60))],
)
async def add_ban(
    room_id: Annotated[
        uuid.UUID,
        Path(
            ...,
            description="ID комнаты, в которой нужно забанить пользователя (или игнорируется для глобального бана).",
        ),
    ],
    user_id: Annotated[
        uuid.UUID, Path(..., description="ID пользователя, которого нужно забанить.")
    ],
    ban_data: BanCreate,
    user: user_dependencies,
    room_service: Annotated[RoomService,Depends(get_room_service)],
) -> BanResponse:
    """
    Банит пользователя в конкретной комнате или глобально.

    Только владелец комнаты может банить в своей комнате.
    (Логика глобального бана пока не реализована на уровне прав, но путь есть)

    Args:
        room_id (uuid.UUID): ID комнаты.
        target_user_id (uuid.UUID): ID пользователя, которого нужно забанить.
        ban_data (BanCreate): Объект с данными бана (причина, room_id).
        db (Session): Сессия базы данных.
        current_user (User): Текущий аутентифицированный пользователь.

    Returns:
        BanResponse: Детали созданной записи о бане.
    """
    return await room_service.ban_user_from_room(room_id, user_id, ban_data, user)


@room.delete(
    "/{room_id}/members/{user_id}/ban",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(RateLimiter(times=5, seconds=60))],
)
async def unban_user(
    room_id: Annotated[
        uuid.UUID,
        Path(
            ...,
            description="ID комнаты, в которой нужно снять бан (или игнорируется для глобального разбана).",
        ),
    ],
    user_id: Annotated[
        uuid.UUID, Path(..., description="ID пользователя, с которого нужно снять бан.")
    ],
    current_user: user_dependencies,
    room_service: Annotated[RoomService,Depends(get_room_service)],
) -> dict[str, Any]:
    """
    Снимает бан с пользователя в конкретной комнате или глобально.

    Только владелец комнаты может снимать баны в своей комнате.
    (Логика глобального разбана пока не реализована на уровне прав)

    Args:
        room_id (uuid.UUID): ID комнаты.
        target_user_id (uuid.UUID): ID пользователя, с которого нужно снять бан.
        db (Session): Сессия базы данных.
        current_user (User): Текущий аутентифицированный пользователь.

    Returns:
        dict: Сообщение об успешном снятии бана.
    """
    return await room_service.unban_user_from_room(room_id, user_id, current_user)


@room.post(
    "/{room_id}/invite/{invited_user_id}",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(RateLimiter(times=5, seconds=60))],
)
async def send_room_invite(
    room_id: Annotated[
        uuid.UUID, Path(..., description="ID комнаты, куда нужно пригласить.")
    ],
    invited_user_id: Annotated[
        uuid.UUID, Path(..., description="ID пользователя, которого нужно пригласить.")
    ],
    current_user: user_dependencies,
    room_service: Annotated[RoomService,Depends(get_room_service)],
) -> dict[str, str]:
    """
    Отправляет приглашение указанному пользователю присоединиться к комнате.
    Только владелец или модератор комнаты может отправлять приглашения.

    Args:
        room_id (uuid.UUID): ID комнаты, куда приглашают.
        invited_user_id (uuid.UUID): ID пользователя, которого приглашают.
        db (Session): Сессия базы данных.
        current_user (User): Текущий аутентифицированный пользователь (отправитель приглашения).

    Returns:
        dict[str, str]: Сообщение об успешной отправке приглашения.
    """
    return await room_service.send_room_invite(room_id, current_user.id, invited_user_id)


@room.put(
    "/{notification_id}/respond-to-invite",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(RateLimiter(times=5, seconds=60))],
)
async def respond_to_room_invite(
    notification_id: Annotated[
        uuid.UUID,
        Path(..., description="ID уведомления-приглашения, на которое нужно ответить."),
    ],
    response_data: InviteResponse,
    current_user: user_dependencies,
    room_service: Annotated[RoomService,Depends(get_room_service)],
) -> dict[str, str]:
    """
    Отвечает на приглашение в комнату (принимает или отклоняет).

    Args:
        notification_id (uuid.UUID): ID уведомления о приглашении.
        response_data (InviteResponse): Данные ответа, содержащие 'action' ("accept" или "decline").
        db (Session): Сессия базы данных.
        current_user (User): Текущий аутентифицированный пользователь (который отвечает на приглашение).

    Returns:
        dict[str, str]: Сообщение о результате операции.
    """
    return await room_service.handle_room_invite_response(
        notification_id, current_user.id, response_data.action
    )


@room.put(
    "/{room_id}/playback-host",
    status_code=status.HTTP_200_OK,
    response_model=dict[str, Any],
)
async def set_room_playback_host(
    room_id: uuid.UUID,
    room_service: Annotated[RoomService,Depends(get_room_service)],
    user_id_to_set_as_host: Annotated[uuid.UUID,Body(..., embed=True)] ,
    current_user: user_dependencies,
    
) -> dict[str, Any]:
    """
    Назначает указанного пользователя хостом воспроизведения для комнаты.
    Только владелец или модератор могут назначить хоста.
    Назначаемый пользователь должен быть авторизован в Spotify и иметь активное устройство.
    """
    return await room_service.set_playback_host(room_id, user_id_to_set_as_host)


@room.put("/{room_id}/player/play", status_code=status.HTTP_204_NO_CONTENT)
async def player_play_command(
    room_id: uuid.UUID,
    current_user: user_dependencies,
    room_service: Annotated[RoomService,Depends(get_room_service)],
    track_uri: str | None = None,
    position_ms: int = 0,
):
    """
    Запускает или возобновляет воспроизведение Spotify в комнате через хоста воспроизведения.
    """
    return await room_service.player_command_play(
        room_id, current_user, track_uri=track_uri, position_ms=position_ms
    )


@room.put("/{room_id}/player/pause", status_code=status.HTTP_204_NO_CONTENT)
async def player_pause_command(
    room_id: uuid.UUID, current_user: user_dependencies,room_service: Annotated[RoomService,Depends(get_room_service)],
):
    """
    Ставит воспроизведение Spotify на паузу в комнате через хоста воспроизведения.
    """
    return await room_service.player_command_pause(room_id, current_user)


@room.post("/{room_id}/player/next", status_code=status.HTTP_204_NO_CONTENT)
async def player_skip_next_command(
    room_id: uuid.UUID, current_user: user_dependencies,room_service: Annotated[RoomService,Depends(get_room_service)],
):
    """
    Переключает на следующий трек в Spotify плеере комнаты через хоста воспроизведения.
    """
    return await room_service.player_command_skip_next(room_id, current_user)


@room.post("/{room_id}/player/previous", status_code=status.HTTP_204_NO_CONTENT)
async def player_skip_previous_command(
    room_id: uuid.UUID, current_user: user_dependencies,room_service: Annotated[RoomService,Depends(get_room_service)],
):
    """
    Переключает на предыдущий трек в Spotify плеере комнаты через хоста воспроизведения.
    """
    return await room_service.player_command_skip_previous(room_id, current_user)


@room.get("/{room_id}/player/state", response_model=dict[str, Any])
async def get_room_player_state(
    room_id: uuid.UUID, current_user: user_dependencies,room_service: Annotated[RoomService,Depends(get_room_service)],
) -> dict[str, Any]:
    """
    Получает текущее состояние Spotify плеера для комнаты.
    """
    return await room_service.get_room_player_state(room_id, current_user)
