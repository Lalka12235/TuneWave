from typing import Annotated

from fastapi import APIRouter, Cookie, status

from app.domain.entity import UserEntity
from app.presentation.schemas.ban_schemas import BanResponse
from app.application.services.ban_service import BanService

from dishka.integrations.fastapi import DishkaRoute,FromDishka,inject

ban = APIRouter(
    tags=['Ban'],
    prefix='/ban',
    route_class=DishkaRoute
)

user_dependencies = FromDishka[UserEntity]
ban_service = FromDishka[BanService]


@ban.get(
    '/my-issued',
    response_model=list[BanResponse],
    status_code=status.HTTP_200_OK,
)
@inject
async def get_bans_by_admin(
    ban_service: ban_service,
    user: user_dependencies,
    session_id: Annotated[str | None, Cookie()] = None,
    
) -> list[BanResponse]:
    """
    Получает список всех банов, которые были выданы текущим аутентифицированным пользователем.

    Args:
        current_user (User): Текущий аутентифицированный пользователь.

    Returns:
        list[BanResponse]: Список объектов BanResponse, представляющих выданные баны.
    """
    user.set_session_id = session_id
    user_from_identity = user.get_current_user()
    return ban_service.get_bans_by_admin(user_from_identity.id)


@ban.get(
    '/my-received',
    response_model=list[BanResponse],
    status_code=status.HTTP_200_OK,
)
@inject
async def get_bans_on_user(
    ban_service: ban_service,
    user: user_dependencies,
    session_id: Annotated[str | None, Cookie()] = None,
) -> list[BanResponse]:
    """
    Получает список всех банов, которые были получены текущим аутентифицированным пользователем.

    Args:
        current_user (User): Текущий аутентифицированный пользователь.

    Returns:
        list[BanResponse]: Список объектов BanResponse, представляющих полученные баны.
    """
    user.set_session_id = session_id
    user_from_identity = user.get_current_user()
    return ban_service.get_bans_on_user(user_from_identity.id)