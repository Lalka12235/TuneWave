from fastapi import APIRouter,Depends,status,Path,Query
from app.schemas.room_schemas import RoomCreate, RoomUpdate, RoomResponse
from typing import Annotated
from app.auth.auth import get_current_user
from app.models.user import User
from app.services.room_service import RoomService
from app.config.session import get_db
from sqlalchemy.orm import Session
import uuid


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
) -> RoomResponse:
    """
    Создает новую комнату.
    Требуется аутентификация. Владелец комнаты будет текущим аутентифицированным пользователем.
    """
    return RoomService.create_room(db, room_data, current_user)


@room.get("/{room_id}", response_model=RoomResponse)
def get_room_by_id(

    room_id: Annotated[uuid.UUID, Path(..., description="Уникальный ID комнаты")], 
    db: db_dependencies
) -> RoomResponse:
    """
    Получает информацию о комнате по ее ID.
    Не требует аутентификации.
    """
    return RoomService.get_room_by_id(db, room_id)



@room.get("/by-name/", response_model=RoomResponse)
def get_room_by_name(
    name: Annotated[str, Query(..., description="Название комнаты")], 
    db: db_dependencies
) -> RoomResponse:
    """
    Получает информацию о комнате по ее названию.
    Не требует аутентификации.
    """
    return RoomService.get_room_by_name(db, name)


@room.get("/", response_model=list[RoomResponse])
def get_all_rooms(
    db: db_dependencies
) -> list[RoomResponse]:
    """
    Получает список всех доступных комнат.
    Не требует аутентификации.
    """
    return RoomService.get_all_rooms(db)


@room.put("/{room_id}", response_model=RoomResponse)
def update_room(
    room_id: Annotated[uuid.UUID, Path(..., description="ID комнаты для обновления")], # ID комнаты из пути URL
    update_data: RoomUpdate,
    db: db_dependencies,
    current_user: user_dependencies
) -> RoomResponse:
    """
    Обновляет информацию о комнате по ее ID.
    Требуется аутентификация. Только владелец комнаты может ее обновить.
    """
    return RoomService.update_room(db, room_id, update_data, current_user)


@room.delete("/{room_id}", status_code=status.HTTP_200_OK)
def delete_room(
    room_id: Annotated[uuid.UUID, Path(..., description="ID комнаты для удаления")], # ID комнаты из пути URL
    db: db_dependencies,
    current_user: user_dependencies 
) -> dict: 
    """
    Удаляет комнату по ее ID.
    Требуется аутентификация. Только владелец комнаты может ее удалить.
    """
    return RoomService.delete_room(db, room_id, current_user)