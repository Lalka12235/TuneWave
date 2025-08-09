from fastapi import APIRouter,Depends, UploadFile,Path
from sqlalchemy.orm import Session
from typing import Annotated
from app.schemas.user_schemas import UserResponse,UserUpdate
from app.services.user_service import UserService
from app.auth.auth import get_current_user
from app.config.session import get_db
from app.models.user import User
from fastapi_limiter.depends import RateLimiter
import uuid


user = APIRouter(
    tags=['User'],
    prefix='/users'
)

db_dependencies = Annotated[Session,Depends(get_db)]
user_dependencies = Annotated[User,Depends(get_current_user)]

@user.get('/me',response_model=UserResponse,dependencies=[Depends(RateLimiter(times=10, seconds=60))])
async def get_me(
    db: db_dependencies,
    user: user_dependencies,
) -> UserResponse:
    """
    Получает профиль текущего аутентифицированного пользователя.
    
    Returns:
        UserResponse: Pydantic-модель с данными профиля пользователя.
    """
    return UserService._map_user_to_response(user)


@user.put('/{user_id}',response_model=UserResponse)
async def update_profile(
    db: db_dependencies,
    user: user_dependencies,
    update_data: UserUpdate
) -> UserResponse:
    """_summary_

    Args:
        db (db_dependencies): _description_
        user (user_dependencies): _description_
        update_data (UserUpdate): _description_

    Returns:
        UserResponse: _description_
    """
    return UserService.update_user_profile(db,user.id,update_data)


@user.post('/me/avatar',response_model=UserResponse,dependencies=[Depends(RateLimiter(times=5, seconds=60))])
async def load_avatar(
    db:db_dependencies,
    user: user_dependencies,
    avatar_file: UploadFile,
) -> UserResponse:
    """
    Загружает новую аватарку для текущего пользователя.

    Args:
        db (Session): Сессия базы данных.
        user (User): Объект текущего аутентифицированного пользователя.
        avatar_file (UploadFile): Загружаемый файл изображения.

    Returns:
        UserResponse: Обновленный профиль пользователя с новым URL аватарки.
    """
    return await UserService.load_avatar(db,user,avatar_file) 


@user.get(
    "/{user_id}",
    response_model=UserResponse,
    dependencies=[Depends(RateLimiter(times=20, seconds=60))]
)
def get_user_by_id(
    user_id: Annotated[uuid.UUID, Path(..., description="Уникальный ID пользователя")],
    db: db_dependencies,
) -> UserResponse:
    """
    Получает публичную информацию о пользователе по его ID.
    Не требует аутентификации, если предназначен для публичного просмотра.
    """
    return UserService.get_user_by_id(db, user_id)