import uuid
from typing import Annotated

from fastapi import APIRouter, Path, UploadFile

from app.domain.entity import UserEntity
from app.infrastructure.redis.redis_service import RedisService
from app.presentation.schemas.user_schemas import UserResponse, UserUpdate

from dishka.integrations.fastapi import DishkaRoute,FromDishka
from app.application.commands.user import UpdateUser,ReadUser
from app.application.commands.avatar import LoadAvatar

user = APIRouter(
    tags=['User'],
    prefix='/users',
    route_class=DishkaRoute
)

user_dependencies = FromDishka[UserEntity]
redis_service = FromDishka[RedisService]

@user.get('/me',response_model=UserResponse)
async def get_me(
    user: user_dependencies,
    redis_client: redis_service,
    interactor: FromDishka[ReadUser],
) -> UserResponse:
    """
    Получает профиль текущего аутентифицированного пользователя.
    """
    cache_key = f'users:get_me:{user.id}'
    async def fetch():
        return interactor.user_mapper.to_response(user)
    return await redis_client.get_or_set(cache_key,fetch,300)

@user.put('/{user_id}',response_model=UserResponse)
async def update_profile(
    user: user_dependencies,
    update_data: UserUpdate,
    interactor: FromDishka[UpdateUser],
) -> UserResponse:
    user_data = update_data.model.dict(exclude_unset=True)
    return await interactor.update_user_profile(user.id,user_data)


@user.post('/me/avatar',response_model=UserResponse)
async def load_avatar(
    user: user_dependencies,
    avatar_file: UploadFile,
    interactor: FromDishka[LoadAvatar],
) -> UserResponse:
    """
    Загружает новую аватарку для текущего пользователя.
    """
    return await interactor.load_avatar(user,avatar_file,avatar_file.content_type,avatar_file.filename)


@user.get(
    "/{user_id}",
    response_model=UserResponse,
)
async def get_user_by_id(
    user_id: Annotated[uuid.UUID, Path(..., description="Уникальный ID пользователя")],
    interactor: FromDishka[ReadUser],
    redis_client: redis_service,
) -> UserResponse:
    """
    Получает публичную информацию о пользователе по его ID.
    Не требует аутентификации, если предназначен для публичного просмотра.
    """
    key = f'users:get_user_by_id:{user_id}'
    async def fetch():
        return await interactor.get_user_by_id(user_id)
    return await redis_client.get_or_set(key,fetch,300)