from fastapi import APIRouter,status
from app.application.commands.ban.read_ban import ReadBan
from app.domain.entity.user import UserEntity
from app.presentation.schemas.ban_schemas import BanResponse

from dishka.integrations.fastapi import DishkaRoute,FromDishka

ban = APIRouter(
    tags=['Ban'],
    prefix='/ban',
    route_class=DishkaRoute
)

@ban.get(
    '/my-issued',
    response_model=list[BanResponse],
    status_code=status.HTTP_200_OK,
)
async def get_bans_by_admin(
    user: FromDishka[UserEntity],
    interactor: FromDishka[ReadBan],
) -> list[BanResponse]:
    """
    Получает список всех банов, которые были выданы текущим аутентифицированным пользователем.
    """
    return interactor.get_bans_by_admin(user.id)


@ban.get(
    '/my-received',
    response_model=list[BanResponse],
    status_code=status.HTTP_200_OK,
)
async def get_bans_on_user(
    user: FromDishka[UserEntity],
    interactor: FromDishka[ReadBan],
) -> list[BanResponse]:
    """
    Получает список всех банов, которые были получены текущим аутентифицированным пользователем.
    """
    return interactor.get_bans_on_user(user.id)