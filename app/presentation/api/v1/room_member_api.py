import uuid
from typing import Annotated, Any

from fastapi import APIRouter,Depends, Path,status
from fastapi_limiter.depends import RateLimiter

from app.domain.entity import UserEntity
from app.presentation.schemas.ban_schemas import BanCreate, BanResponse
from app.presentation.schemas.room_member_schemas import JoinRoomRequest,RoomMemberResponse,RoomMemberRoleUpdate
from app.presentation.schemas.room_schemas import (
    InviteResponse,
    RoomResponse,
)
from app.presentation.schemas.user_schemas import UserResponse
from app.application.services.room_member_service import RoomMemberService

from app.application.services.redis_service import RedisService

from dishka import FromDishka

room_member = APIRouter(tags=["Room"], prefix="/rooms")

user_dependencies = FromDishka[UserEntity]
room_member_service = FromDishka[RoomMemberService]
redis_service = FromDishka[RedisService]


async def join_room(
    room_id: Annotated[
        uuid.UUID,
        Path(..., description="ID комнаты, к которой присоединяется пользователь"),
    ],
    current_user: user_dependencies,
    request_data: JoinRoomRequest,
    room_member_service: room_member_service,
) -> RoomResponse:
    """
    Пользователь присоединяется к комнате.
    Требуется аутентификация. Если комната приватная, требуется пароль.
    """
    return await room_member_service.join_room(current_user, room_id, request_data.password)



@room_member.post("/{room_id}/leave", status_code=status.HTTP_200_OK)
async def leave_room(
    room_id: Annotated[
        uuid.UUID, Path(..., description="ID комнаты, которую покидает пользователь")
    ],
    current_user: user_dependencies,
    room_member_service: room_member_service,
) -> dict:
    """
    Пользователь покидает комнату.
    Требуется аутентификация.
    """
    return await room_member_service.leave_room(room_id, current_user)


@room_member.get(
    "/{room_id}/members",
    response_model=list[UserResponse],
    dependencies=[Depends(RateLimiter(times=10, seconds=60))],
)
async def get_room_members(
    room_id: Annotated[
        uuid.UUID, Path(..., description="ID комнаты для получения списка участников")
    ],
    room_member_service: room_member_service,
    redis_client: redis_service,
    
) -> list[UserResponse]:
    """
    Получает список всех участников комнаты.
    Не требует аутентификации.
    """
    key = f'rooms_member:get_room_member:{room_id}'
    async def fetch():
        return await room_member_service.get_room_members(room_id)
    return await redis_client.get_or_set(key,fetch,300)


@room_member.post(
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
    room_member_service: room_member_service,
) -> BanResponse:
    """
    Банит пользователя в конкретной комнате или глобально.

    Только владелец комнаты может банить в своей комнате.
    (Логика глобального бана пока не реализована на уровне прав, но путь есть)

    Args:
        room_id (uuid.UUID): ID комнаты.
        target_user_id (uuid.UUID): ID пользователя, которого нужно забанить.
        ban_data (BanCreate): Объект с данными бана (причина, room_id).
        current_user (User): Текущий аутентифицированный пользователь.

    Returns:
        BanResponse: Детали созданной записи о бане.
    """
    ban_data = ban_data.model_dump()
    return await room_member_service.ban_user_from_room(room_id, user_id, ban_data, user)


@room_member.delete(
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
    room_member_service: room_member_service,
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
    return await room_member_service.unban_user_from_room(room_id, user_id, current_user)


@room_member.post(
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
    room_member_service: room_member_service,
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
    return await room_member_service.send_room_invite(room_id, current_user.id, invited_user_id)


@room_member.put(
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
    room_member_service: room_member_service,
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
    return await room_member_service.handle_room_invite_response(
        notification_id, current_user.id, response_data.action
    )

@room_member.put(
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
    room_member_service: room_member_service,
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
    return await room_member_service.update_member_role(
        room_id, target_user_id, new_role.role, user
    )