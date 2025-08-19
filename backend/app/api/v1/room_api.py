from fastapi import APIRouter,Depends,status,Path,Query
from app.schemas.room_schemas import (
    RoomCreate, 
    RoomUpdate, 
    RoomResponse,
    TrackInQueueResponse,
    AddTrackToQueueRequest,
    InviteResponse
)
from app.schemas.user_schemas import UserResponse
from app.schemas.room_member_schemas import RoomMemberResponse,RoomMemberRoleUpdate,JoinRoomRequest
from typing import Annotated,Any
from app.auth.auth import get_current_user
from app.models.user import User
from app.services.room_service import RoomService
from app.config.session import get_db
from sqlalchemy.orm import Session
import uuid
from fastapi_limiter.depends import RateLimiter
from app.schemas.ban_schemas import BanCreate,BanResponse

room = APIRouter(
    tags=['Room'],
    prefix='/rooms'
)

db_dependencies = Annotated[Session,Depends(get_db)]
user_dependencies = Annotated[User,Depends(get_current_user)]




@room.post('/',response_model=RoomResponse,status_code=status.HTTP_201_CREATED,dependencies=[Depends(RateLimiter(times=5, seconds=60))])
async def create_room(
    room_data: RoomCreate,
    db: db_dependencies,
    current_user: user_dependencies,
) -> RoomResponse:
    """
    Создает новую комнату.
    Требуется аутентификация. Владелец комнаты будет текущим аутентифицированным пользователем.
    """
    return await RoomService.create_room(db, room_data, current_user)


@room.put("/{room_id}", response_model=RoomResponse,dependencies=[Depends(RateLimiter(times=10, seconds=60))])
def update_room(
    room_id: Annotated[uuid.UUID, Path(..., description="ID комнаты для обновления")],
    update_data: RoomUpdate,
    db: db_dependencies,
    current_user: user_dependencies,
) -> RoomResponse:
    """
    Обновляет информацию о комнате по ее ID.
    Требуется аутентификация. Только владелец комнаты может ее обновить.
    """
    return RoomService.update_room(db, room_id, update_data, current_user)


@room.delete("/{room_id}", status_code=status.HTTP_200_OK,dependencies=[Depends(RateLimiter(times=10, seconds=60))])
def delete_room(
    room_id: Annotated[uuid.UUID, Path(..., description="ID комнаты для удаления")],
    db: db_dependencies,
    current_user: user_dependencies,
) -> dict:
    """
    Удаляет комнату по ее ID.
    Требуется аутентификация. Только владелец комнаты может ее удалить.
    """
    return RoomService.delete_room(db, room_id, current_user)

@room.post('/{room_id}/join',response_model=RoomResponse,status_code=status.HTTP_200_OK,dependencies=[Depends(RateLimiter(times=10, seconds=60))])
async def join_room(
    room_id: Annotated[uuid.UUID, Path(..., description="ID комнаты, к которой присоединяется пользователь")],
    db: db_dependencies,
    current_user: user_dependencies,
    request_data: JoinRoomRequest,
) -> RoomResponse:
    """
    Пользователь присоединяется к комнате.
    Требуется аутентификация. Если комната приватная, требуется пароль.
    """
    return await RoomService.join_room(db,current_user,room_id,request_data.password)


@room.post('/{room_id}/leave',status_code=status.HTTP_200_OK)
async def leave_room(
    room_id: Annotated[uuid.UUID, Path(..., description="ID комнаты, которую покидает пользователь")],
    db: db_dependencies,
    current_user: user_dependencies,
) -> dict:
    """
    Пользователь покидает комнату.
    Требуется аутентификация.
    """
    return await RoomService.leave_room(db,room_id,current_user)


@room.get('/{room_id}/members',response_model=list[UserResponse],dependencies=[Depends(RateLimiter(times=10, seconds=60))])
async def get_room_members(
    room_id: Annotated[uuid.UUID, Path(..., description="ID комнаты для получения списка участников")],
    db: db_dependencies,
) -> list[UserResponse]:
    """
    Получает список всех участников комнаты.
    Не требует аутентификации.
    """
    return RoomService.get_room_members(db,room_id)


@room.get("/by-name/", response_model=RoomResponse,dependencies=[Depends(RateLimiter(times=10, seconds=60))])
def get_room_by_name(
    name: Annotated[str, Query(..., description="Название комнаты")], 
    db: db_dependencies,
) -> RoomResponse:
    """
    Получает информацию о комнате по ее названию.
    Не требует аутентификации.
    """
    return RoomService.get_room_by_name(db, name)


@room.get("/my-rooms", response_model=list[RoomResponse],dependencies=[Depends(RateLimiter(times=10, seconds=60))])
async def get_my_rooms(
    db: db_dependencies,
    current_user: user_dependencies,
) -> list[RoomResponse]:
    """
    Получает список всех комнат, в которых состоит текущий аутентифицированный пользователь.
    Требуется аутентификация.
    """
    return RoomService.get_user_rooms(db, current_user)

@room.get("/", response_model=list[RoomResponse],dependencies=[Depends(RateLimiter(times=10, seconds=60))])
def get_all_rooms(
    db: db_dependencies,
) -> list[RoomResponse]:
    """
    Получает список всех доступных комнат.
    Не требует аутентификации.
    """
    return RoomService.get_all_rooms(db)


@room.get("/{room_id}", response_model=RoomResponse,dependencies=[Depends(RateLimiter(times=10, seconds=60))])
def get_room_by_id(
    room_id: Annotated[uuid.UUID, Path(..., description="Уникальный ID комнаты")], 
    db: db_dependencies,
) -> RoomResponse:
    """
    Получает информацию о комнате по ее ID.
    Не требует аутентификации.
    """
    return RoomService.get_room_by_id(db, room_id)


@room.post('/{room_id}/queue', response_model=TrackInQueueResponse, status_code=status.HTTP_201_CREATED,dependencies=[Depends(RateLimiter(times=10, seconds=60))])
async def add_track_to_queue(
    db: db_dependencies,
    current_user: user_dependencies,
    request: AddTrackToQueueRequest,
    room_id: Annotated[uuid.UUID,Path(...,description='Уникальный ID комнаты')],
) -> TrackInQueueResponse:
    """
    Добавляет трек в очередь комнаты. Только владелец комнаты может это сделать.
    """
    association = await RoomService.add_track_to_queue(
        db=db,
        room_id=room_id,
        track_spotify_id=request.spotify_id,
        current_user=current_user
    )
    return association


@room.get('/{room_id}/queue/{association_id}',response_model=list[TrackInQueueResponse],dependencies=[Depends(RateLimiter(times=10, seconds=60))])
async def get_room_queue(
    db: db_dependencies,
    room_id: Annotated[uuid.UUID,Path(...,description='Уникальный ID комнаты')],
) -> list[TrackInQueueResponse]:
    """
    Получает текущую очередь треков для комнаты.
    """
    return RoomService.get_room_queue(db,room_id)


@room.delete('/{room_id}/queue/{association_id}',dependencies=[Depends(RateLimiter(times=10, seconds=60))])
async def remove_track_from_queue(
    db: db_dependencies,
    current_user: user_dependencies,
    room_id: Annotated[uuid.UUID,Path(...,description='Уникальный ID комнаты')],
    association_id: Annotated[uuid.UUID, Path(..., description="ID ассоциации трека в очереди")],
) -> dict:
    """
    Удаляет трек из очереди комнаты по ID ассоциации. Только владелец комнаты может это сделать.
    """
    return await RoomService.remove_track_from_queue(db,room_id,association_id,current_user.id)


@room.put('/{room_id}/members/{target_user_id}/role',response_model=RoomMemberResponse,dependencies=[Depends(RateLimiter(times=5, seconds=60))])
async def update_member_role(
    room_id: Annotated[uuid.UUID, Path(..., description="ID комнаты, к которой присоединяется пользователь")],
    db: db_dependencies,
    target_user_id: Annotated[uuid.UUID, Path(..., description="ID пользователя, чью роль нужно изменить")],
    user: user_dependencies,
    new_role: RoomMemberRoleUpdate
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
    return await RoomService.update_member_role(db,room_id,target_user_id,new_role.role,user)


@room.post(
    '/{room_id}/members/{user_id}/ban',
    response_model=BanResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RateLimiter(times=5, seconds=60))]
)
async def add_ban(
    room_id: Annotated[uuid.UUID, Path(..., description="ID комнаты, в которой нужно забанить пользователя (или игнорируется для глобального бана).")],
    user_id: Annotated[uuid.UUID, Path(..., description="ID пользователя, которого нужно забанить.")],
    ban_data: BanCreate,
    db: db_dependencies,
    user: user_dependencies
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
    return await RoomService.ban_user_from_room(db,room_id,user_id,ban_data,user)


@room.delete(
    '/{room_id}/members/{user_id}/ban',
    response_model=dict[str,Any],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(RateLimiter(times=5, seconds=60))],
)
async def unban_user(
    room_id: Annotated[uuid.UUID, Path(..., description="ID комнаты, в которой нужно снять бан (или игнорируется для глобального разбана).")],
    user_id: Annotated[uuid.UUID, Path(..., description="ID пользователя, с которого нужно снять бан.")],
    db: db_dependencies,
    current_user: user_dependencies,
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
    return await RoomService.unban_user_from_room(db,room_id,user_id,current_user)



@room.post(
    '/{room_id}/invite/{invited_user_id}',
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(RateLimiter(times=5, seconds=60))]
)
async def send_room_invite(
    room_id: Annotated[uuid.UUID, Path(..., description="ID комнаты, куда нужно пригласить.")],
    invited_user_id: Annotated[uuid.UUID, Path(..., description="ID пользователя, которого нужно пригласить.")],
    db: db_dependencies,
    current_user: user_dependencies,
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
    return await RoomService.send_room_invite(
        db, room_id, current_user.id, invited_user_id
    )


@room.put(
    '/{notification_id}/respond-to-invite',
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(RateLimiter(times=5, seconds=60))]
)
async def respond_to_room_invite(
    notification_id: Annotated[uuid.UUID, Path(..., description="ID уведомления-приглашения, на которое нужно ответить.")],
    response_data: InviteResponse,
    db: db_dependencies,
    current_user: user_dependencies,
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
    return await RoomService.handle_room_invite_response(
        db, notification_id, current_user.id, response_data.action
    )