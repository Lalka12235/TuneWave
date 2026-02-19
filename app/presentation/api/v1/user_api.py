import uuid
from typing import Annotated

from fastapi import APIRouter, Path, UploadFile, Cookie,Depends

#from app.domain.entity import UserEntity
from app.presentation.schemas.user_schemas import UserResponse, UserUpdate
from app.application.services.user_service import UserService
from app.application.services.redis_service import RedisService

from dishka.integrations.fastapi import DishkaRoute,FromDishka,inject
from app.application.services.indentity_provider import IndentityProvider
from app.presentation.dependencies import get_indentity_provider

user = APIRouter(
    tags=['User'],
    prefix='/users',
    route_class=DishkaRoute
)

current_user = Annotated[IndentityProvider,Depends(get_indentity_provider)]
redis_service = FromDishka[RedisService]
user_service = FromDishka[UserService]

@user.get('/me',response_model=UserResponse)
@inject
async def get_me(
    user: current_user,
    redis_client: redis_service,
    user_service: user_service,
    session_id: Annotated[str | None, Cookie()] = None,
    
) -> UserResponse:
    """
    Получает профиль текущего аутентифицированного пользователя.
    
    Returns:
        UserResponse: Pydantic-модель с данными профиля пользователя.
    """
    user.set_session_id = session_id
    user_from_identity = user.get_current_user()
    cache_key = f'users:get_me:{user_from_identity.id}'
    async def fetch():
        return user_service.user_mapper.to_response(user_from_identity)
    return await redis_client.get_or_set(cache_key,fetch,300)

@user.put('/{user_id}',response_model=UserResponse)
@inject
async def update_profile(
    user: current_user,
    update_data: UserUpdate,
    user_service: user_service,
    session_id: Annotated[str | None, Cookie()] = None,
) -> UserResponse:
    """_summary_

    Args:
        user (current_user): _description_
        update_data (UserUpdate): _description_

    Returns:
        UserResponse: _description_
    """
    user.set_session_id = session_id
    user.set_session_id = session_id
    user_from_identity = user.get_current_user()
    user_data = update_data.model.dict(exclude_unset=True)
    return await user_service.update_user_profile(user_from_identity.id,user_data)


@user.post('/me/avatar',response_model=UserResponse)
@inject
async def load_avatar(
    user: current_user,
    avatar_file: UploadFile,
    user_service: user_service,
    session_id: Annotated[str | None, Cookie()] = None,
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
    user.set_session_id = session_id
    user_from_identity = user.get_current_user()    
    return await user_service.load_avatar(user_from_identity,avatar_file,avatar_file.content_type,avatar_file.filename)


@user.get(
    "/{user_id}",
    response_model=UserResponse,
)
@inject
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