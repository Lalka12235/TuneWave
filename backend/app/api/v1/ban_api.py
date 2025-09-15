from fastapi import APIRouter,Depends,status
from app.schemas.ban_schemas import BanResponse
from app.services.ban_service import BanService
from typing import Annotated
from app.auth.auth import get_current_user
from app.models import User
from app.config.session import get_db
from sqlalchemy.orm import Session
from fastapi_limiter.depends import RateLimiter

ban = APIRouter(
    tags=['Ban'],
    prefix='/ban'
)

db_dependencies = Annotated[Session,Depends(get_db)]
user_dependencies = Annotated[User,Depends(get_current_user)]


@ban.get(
    '/my-issued',
    response_model=list[BanResponse],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(RateLimiter(times=15, seconds=60))],
)
async def get_bans_by_admin(
    db: db_dependencies,
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
    return BanService.get_bans_by_admin(db,user.id)


@ban.get(
    '/my-received',
    response_model=list[BanResponse],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(RateLimiter(times=15, seconds=60))],
)
async def get_bans_on_user(
    db: db_dependencies,
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
    return BanService.get_bans_on_user(db,user.id)