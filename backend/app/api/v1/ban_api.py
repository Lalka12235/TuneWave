from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi_limiter.depends import RateLimiter

from app.auth.auth import get_current_user
from app.schemas.entity import UserEntity
from app.schemas.ban_schemas import BanResponse
from app.services.ban_service import BanService
from app.services.dep import get_ban_service

ban = APIRouter(
    tags=['Ban'],
    prefix='/ban'
)

user_dependencies = Annotated[UserEntity,Depends(get_current_user)]


@ban.get(
    '/my-issued',
    response_model=list[BanResponse],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(RateLimiter(times=15, seconds=60))],
)
async def get_bans_by_admin(
    ban_service: Annotated[BanService,Depends(get_ban_service)],
    user: user_dependencies,
    
) -> list[BanResponse]:
    """
    Получает список всех банов, которые были выданы текущим аутентифицированным пользователем.

    Args:
        db (Session): Сессия базы данных.
        current_user (User): Текущий аутентифицированный пользователь.

    Returns:
        list[BanResponse]: Список объектов BanResponse, представляющих выданные баны.
    """
    return ban_service.get_bans_by_admin(user.id)


@ban.get(
    '/my-received',
    response_model=list[BanResponse],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(RateLimiter(times=15, seconds=60))],
)
async def get_bans_on_user(
    ban_service: Annotated[BanService,Depends(get_ban_service)],
    user: user_dependencies,
) -> list[BanResponse]:
    """
    Получает список всех банов, которые были получены текущим аутентифицированным пользователем.

    Args:
        db (Session): Сессия базы данных.
        current_user (User): Текущий аутентифицированный пользователь.

    Returns:
        list[BanResponse]: Список объектов BanResponse, представляющих полученные баны.
    """
    return ban_service.get_bans_on_user(user.id)