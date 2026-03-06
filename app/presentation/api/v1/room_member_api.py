import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Path,status

from app.domain.entity import UserEntity
from app.infrastructure.redis.redis_service import RedisService
from app.presentation.schemas.ban_schemas import BanCreate, BanResponse
from app.presentation.schemas.room_member_schemas import JoinRoomRequest,RoomMemberResponse,RoomMemberRoleUpdate
from app.presentation.schemas.room_schemas import (
    InviteResponse,
    RoomResponse,
)
from app.presentation.schemas.user_schemas import UserResponse
from dishka.integrations.fastapi import DishkaRoute,FromDishka
from app.application.commands.room_member import JoinRoom,ReadMember,SendRoomInvite,LeaveRoom,HandleRoomInvite,BanUserInRoom,UnbanUserInRoom,UpdateMemberRole

room_member = APIRouter(tags=["Room"], prefix="/rooms",route_class=DishkaRoute)

user_dependencies = FromDishka[UserEntity]
redis_service = FromDishka[RedisService]


@room_member.post(
    "/{room_id}/join",
    response_model=RoomResponse,
    status_code=status.HTTP_200_OK,
)
async def join_room(
    room_id: Annotated[
        uuid.UUID,
        Path(..., description="ID комнаты, к которой присоединяется пользователь"),
    ],
    current_user: user_dependencies,
    request_data: JoinRoomRequest,
    interactor: FromDishka[JoinRoom],
) -> RoomResponse:
    """
    Пользователь присоединяется к комнате.
    Требуется аутентификация. Если комната приватная, требуется пароль.
    """
    return await interactor.join_room(current_user, room_id, request_data.password)



@room_member.post("/{room_id}/leave", status_code=status.HTTP_200_OK)
async def leave_room(
    room_id: Annotated[
        uuid.UUID, Path(..., description="ID комнаты, которую покидает пользователь")
    ],
    current_user: user_dependencies,
    interactor: FromDishka[LeaveRoom],
) -> dict:
    """
    Пользователь покидает комнату.
    Требуется аутентификация.
    """
    return await interactor.leave_room(room_id, current_user)


@room_member.get(
    "/{room_id}/members",
    response_model=list[UserResponse],
)
async def get_room_members(
    room_id: Annotated[
        uuid.UUID, Path(..., description="ID комнаты для получения списка участников")
    ],
    interactor: FromDishka[ReadMember],
    redis_client: redis_service,
) -> list[UserResponse]:
    """
    Получает список всех участников комнаты.
    Не требует аутентификации.
    """
    key = f'rooms_member:get_room_member:{room_id}'
    async def fetch():
        return await interactor.get_room_members(room_id)
    return await redis_client.get_or_set(key,fetch,300)


@room_member.post(
    "/{room_id}/members/{user_id}/ban",
    response_model=BanResponse,
    status_code=status.HTTP_201_CREATED,
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
    interactor: FromDishka[BanUserInRoom],
) -> BanResponse:
    """
    Банит пользователя в конкретной комнате или глобально.

    Только владелец комнаты может банить в своей комнате.
    """
    ban_data = ban_data.model_dump()
    return await interactor.ban_user_from_room(room_id, user_id, ban_data, user)


@room_member.delete(
    "/{room_id}/members/{user_id}/ban",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
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
    interactor: FromDishka[UnbanUserInRoom],
) -> dict[str, Any]:
    """
    Снимает бан с пользователя в конкретной комнате или глобально.

    Только владелец комнаты может снимать баны в своей комнате.
    """
    return await interactor.unban_user_from_room(room_id, user_id, current_user)


@room_member.post(
    "/{room_id}/invite/{invited_user_id}",
    status_code=status.HTTP_200_OK,
)
async def send_room_invite(
    room_id: Annotated[
        uuid.UUID, Path(..., description="ID комнаты, куда нужно пригласить.")
    ],
    invited_user_id: Annotated[
        uuid.UUID, Path(..., description="ID пользователя, которого нужно пригласить.")
    ],
    current_user: user_dependencies,
    interactor: FromDishka[SendRoomInvite],
) -> dict[str, str]:
    """
    Отправляет приглашение указанному пользователю присоединиться к комнате.
    Только владелец или модератор комнаты может отправлять приглашения.
    """
    return await interactor.send_room_invite(room_id, current_user.id, invited_user_id)


@room_member.put(
    "/{notification_id}/respond-to-invite",
    status_code=status.HTTP_200_OK,
)
async def respond_to_room_invite(
    notification_id: Annotated[
        uuid.UUID,
        Path(..., description="ID уведомления-приглашения, на которое нужно ответить."),
    ],
    response_data: InviteResponse,
    current_user: user_dependencies,
    interactor: FromDishka[HandleRoomInvite],
) -> dict[str, str]:
    """
    Отвечает на приглашение в комнату (принимает или отклоняет).
    """
    return await interactor.handle_room_invite_response(
        notification_id, current_user.id, response_data.action
    )

@room_member.put(
    "/{room_id}/members/{target_user_id}/role",
    response_model=RoomMemberResponse,
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
    interactor: FromDishka[UpdateMemberRole],
) -> RoomMemberResponse:
    """
    Изменяет роль члена комнаты. Доступно только владельцу комнаты.
    """
    return await interactor.update_member_role(
        room_id, target_user_id, new_role.role, user
    )