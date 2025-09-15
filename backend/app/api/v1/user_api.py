from fastapi import APIRouter,Depends, UploadFile,Path
from sqlalchemy.orm import Session
from typing import Annotated
from app.schemas.user_schemas import UserResponse,UserUpdate
from app.services.user_service import UserService
from app.auth.auth import get_current_user
from app.config.session import get_db
from app.models import User
from fastapi_limiter.depends import RateLimiter
import uuid
from infrastructure.redis.redis import get_redis_client
from redis.asyncio import Redis
from app.logger.log_config import logger
import json
from typing import Callable


user = APIRouter(
    tags=['User'],
    prefix='/users'
)

db_dependencies = Annotated[Session,Depends(get_db)]
user_dependencies = Annotated[User,Depends(get_current_user)]

def cache(key_generator: Callable, expiration: int = 300):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Извлекаем redis_client из kwargs (он будет добавлен FastAPI)
            redis_client: Redis = kwargs.get('redis_client')
            
            # Если Redis недоступен, выполняем функцию без кэширования
            if not redis_client:
                logger.warning("Redis client not available, skipping cache...")
                return await func(*args, **kwargs)

            # ✅ Используем переданную функцию-генератор для создания ключа
            try:
                cache_key = key_generator(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error generating cache key: {e}. Skipping cache...", exc_info=True)
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



@user.get('/me',response_model=UserResponse,dependencies=[Depends(RateLimiter(times=10, seconds=60))])
@cache(key_generator=lambda user, **kwargs: f"user_me:{user.id}", expiration=300)
async def get_me(
    user: user_dependencies,
    redis_client: Redis = Depends(get_redis_client) 
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
@cache(key_generator=lambda user_id, **kwargs: f"user_profile:{user_id}", expiration=300)
async def get_user_by_id(
    user_id: Annotated[uuid.UUID, Path(..., description="Уникальный ID пользователя")],
    db: db_dependencies,
    redis_client: Redis = Depends(get_redis_client) 
) -> UserResponse:
    """
    Получает публичную информацию о пользователе по его ID.
    Не требует аутентификации, если предназначен для публичного просмотра.
    """
    return await UserService.get_user_by_id(db, user_id)