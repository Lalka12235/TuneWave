from fastapi import APIRouter,Depends,status,Path,Query
from app.schemas.room_schemas import (
    RoomCreate, 
    RoomUpdate, 
    RoomResponse,
    TrackInQueueResponse,
    AddTrackToQueueRequest
)
from app.schemas.user_schemas import UserResponse
from app.schemas.room_member_schemas import JoinRoomRequest
from typing import Annotated
from app.auth.auth import get_current_user
from app.models.user import User
from app.services.room_service import RoomService
from app.config.session import get_db
from sqlalchemy.orm import Session
import uuid
from fastapi_limiter.depends import RateLimiter


room = APIRouter(
    tags=['Room'],
    prefix='/rooms'
)

db_dependencies = Annotated[Session,Depends(get_db)]
user_dependencies = Annotated[User,Depends(get_current_user)]




@room.post('/',response_model=RoomResponse,status_code=status.HTTP_201_CREATED)
async def create_room(
    room_data: RoomCreate,
    db: db_dependencies,
    current_user: user_dependencies,
    dependencies=[Depends(RateLimiter(times=5, seconds=60))]
) -> RoomResponse:
    """
    Создает новую комнату.
    Требуется аутентификация. Владелец комнаты будет текущим аутентифицированным пользователем.
    """
    return RoomService.create_room(db, room_data, current_user)


@room.put("/{room_id}", response_model=RoomResponse)
def update_room(
    room_id: Annotated[uuid.UUID, Path(..., description="ID комнаты для обновления")],
    update_data: RoomUpdate,
    db: db_dependencies,
    current_user: user_dependencies,
    dependencies=[Depends(RateLimiter(times=10, seconds=60))]
) -> RoomResponse:
    """
    Обновляет информацию о комнате по ее ID.
    Требуется аутентификация. Только владелец комнаты может ее обновить.
    """
    return RoomService.update_room(db, room_id, update_data, current_user)


@room.delete("/{room_id}", status_code=status.HTTP_200_OK)
def delete_room(
    room_id: Annotated[uuid.UUID, Path(..., description="ID комнаты для удаления")],
    db: db_dependencies,
    current_user: user_dependencies,
    dependencies=[Depends(RateLimiter(times=10, seconds=60))]
) -> dict:
    """
    Удаляет комнату по ее ID.
    Требуется аутентификация. Только владелец комнаты может ее удалить.
    """
    return RoomService.delete_room(db, room_id, current_user)

@room.post('/{room_id}/join',response_model=RoomResponse,status_code=status.HTTP_200_OK)
async def join_room(
    room_id: Annotated[uuid.UUID, Path(..., description="ID комнаты, к которой присоединяется пользователь")],
    db: db_dependencies,
    current_user: user_dependencies,
    request_data: JoinRoomRequest,
    dependencies=[Depends(RateLimiter(times=10, seconds=60))]
) -> RoomResponse:
    """
    Пользователь присоединяется к комнате.
    Требуется аутентификация. Если комната приватная, требуется пароль.
    """
    return RoomService.join_room(db,current_user,room_id,request_data.password)


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
    return RoomService.leave_room(db,room_id,current_user)


@room.get('/{room_id}/members',response_model=list[UserResponse])
async def get_room_members(
    room_id: Annotated[uuid.UUID, Path(..., description="ID комнаты для получения списка участников")],
    db: db_dependencies,
    dependencies=[Depends(RateLimiter(times=10, seconds=60))]
) -> list[UserResponse]:
    """
    Получает список всех участников комнаты.
    Не требует аутентификации.
    """
    return RoomService.get_room_members(db,room_id)


@room.get("/by-name/", response_model=RoomResponse)
def get_room_by_name(
    name: Annotated[str, Query(..., description="Название комнаты")], 
    db: db_dependencies,
    dependencies=[Depends(RateLimiter(times=10, seconds=60))]
) -> RoomResponse:
    """
    Получает информацию о комнате по ее названию.
    Не требует аутентификации.
    """
    return RoomService.get_room_by_name(db, name)


@room.get("/my-rooms", response_model=list[RoomResponse])
async def get_my_rooms(
    db: db_dependencies,
    current_user: user_dependencies,
    dependencies=[Depends(RateLimiter(times=10, seconds=60))]
) -> list[RoomResponse]:
    """
    Получает список всех комнат, в которых состоит текущий аутентифицированный пользователь.
    Требуется аутентификация.
    """
    return RoomService.get_user_rooms(db, current_user)

@room.get("/", response_model=list[RoomResponse])
def get_all_rooms(
    db: db_dependencies,
    dependencies=[Depends(RateLimiter(times=10, seconds=60))]
) -> list[RoomResponse]:
    """
    Получает список всех доступных комнат.
    Не требует аутентификации.
    """
    return RoomService.get_all_rooms(db)


@room.get("/{room_id}", response_model=RoomResponse)
def get_room_by_id(
    room_id: Annotated[uuid.UUID, Path(..., description="Уникальный ID комнаты")], 
    db: db_dependencies,
    dependencies=[Depends(RateLimiter(times=10, seconds=60))]
) -> RoomResponse:
    """
    Получает информацию о комнате по ее ID.
    Не требует аутентификации.
    """
    return RoomService.get_room_by_id(db, room_id)


@room.post('/{room_id}/queue', response_model=TrackInQueueResponse, status_code=status.HTTP_201_CREATED)
async def add_track_to_queue(
    db: db_dependencies,
    current_user: user_dependencies,
    request: AddTrackToQueueRequest,
    room_id: Annotated[uuid.UUID,Path(...,description='Уникальный ID комнаты')],
    dependencies=[Depends(RateLimiter(times=10, seconds=30))]
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


@room.get('/{room_id}/queue/{association_id}',response_model=list[TrackInQueueResponse])
async def get_room_queue(
    db: db_dependencies,
    room_id: Annotated[uuid.UUID,Path(...,description='Уникальный ID комнаты')],
    dependencies=[Depends(RateLimiter(times=10, seconds=60))]
) -> list[TrackInQueueResponse]:
    """
    Получает текущую очередь треков для комнаты.
    """
    return RoomService.get_room_queue(db,room_id)


@room.delete('/{room_id}/queue/{association_id}')
async def remove_track_from_queue(
    db: db_dependencies,
    current_user: user_dependencies,
    room_id: Annotated[uuid.UUID,Path(...,description='Уникальный ID комнаты')],
    association_id: Annotated[uuid.UUID, Path(..., description="ID ассоциации трека в очереди")],
    dependencies=[Depends(RateLimiter(times=10, seconds=60))]
) -> dict:
    """
    Удаляет трек из очереди комнаты по ID ассоциации. Только владелец комнаты может это сделать.
    """
    return await RoomService.remove_track_from_queue(db,room_id,association_id,current_user.id)