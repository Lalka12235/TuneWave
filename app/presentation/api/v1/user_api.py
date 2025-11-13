import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Path, UploadFile
from fastapi_limiter.depends import RateLimiter

from app.presentation.auth.auth import get_current_user
from app.domain.entity import UserEntity
from app.presentation.schemas.user_schemas import UserResponse, UserUpdate
from app.application.services.dep import get_user_service
from app.application.services.user_service import UserService
from app.application.services.redis_service import RedisService
from app.application.services.dep import get_redis_client

user = APIRouter(
    tags=['User'],
    prefix='/users'
)

user_dependencies = Annotated[UserEntity,Depends(get_current_user)]
redis_service = Annotated[RedisService,Depends(get_redis_client)]
user_service = Annotated[UserService,Depends(get_user_service)]

@user.get('/me',response_model=UserResponse,dependencies=[Depends(RateLimiter(times=10, seconds=60))])
async def get_me(
    user: user_dependencies,
    redis_client: redis_service,
    user_service: user_service,
    
) -> UserResponse:
    """
    Получает профиль текущего аутентифицированного пользователя.
    
    Returns:
        UserResponse: Pydantic-модель с данными профиля пользователя.
    """
    cache_key = f'users:get_me:{user.id}'
    async def fetch():
        return user_service.user_mapper.to_response(user)
    return await redis_client.get_or_set(cache_key,fetch,300)

@user.put('/{user_id}',response_model=UserResponse)
async def update_profile(
    user: user_dependencies,
    update_data: UserUpdate,
    user_service: user_service
) -> UserResponse:
    """_summary_

    Args:
        db (db_dependencies): _description_
        user (user_dependencies): _description_
        update_data (UserUpdate): _description_

    Returns:
        UserResponse: _description_
    """
    return user_service.update_user_profile(user.id,update_data)


@user.post('/me/avatar',response_model=UserResponse,dependencies=[Depends(RateLimiter(times=5, seconds=60))])
async def load_avatar(
    user: user_dependencies,
    avatar_file: UploadFile,
    user_service: user_service
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
    return await user_service.load_avatar(user,avatar_file) 


@user.get(
    "/{user_id}",
    response_model=UserResponse,
    dependencies=[Depends(RateLimiter(times=20, seconds=60))],
)
async def get_user_by_id(
    user_id: Annotated[uuid.UUID, Path(..., description="Уникальный ID пользователя")],
    user_service: user_service,
    redis_client: redis_service,
) -> UserResponse:
    """
    Получает публичную информацию о пользователе по его ID.
    Не требует аутентификации, если предназначен для публичного просмотра.
    """
    key = f'users:get_user_by_id:{user_id}'
    async def fetch():
        return await user_service.get_user_by_id(user_id)
    return await redis_client.get_or_set(key,fetch,300)