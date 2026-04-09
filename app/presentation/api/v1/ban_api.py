from fastapi import APIRouter,status
from app.application.commands.ban.read_ban import ReadBan
from app.domain.entity.user import UserEntity
from app.presentation.schemas.ban_schemas import BanResponse
from app.domain.entity import BanEntity

from dishka.integrations.fastapi import DishkaRoute,FromDishka

ban = APIRouter(
    tags=['Ban'],
    prefix='/ban',
    route_class=DishkaRoute
)

def convert_entity_to_schema(entity: BanEntity) -> BanResponse:
    return BanResponse(
        id=entity.id,
        ban_user_id=entity.ban_user_id,
        room_id=entity.room_id,
        reason=entity.reason,
        ban_date=entity.ban_date,
        by_ban_user_id=entity.by_ban_user_id,
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
    result = interactor.get_bans_by_admin(user.id)
    lst_result = [convert_entity_to_schema(res) for res in result]
    return lst_result


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
    result = interactor.get_bans_on_user(user.id)
    lst_result = [convert_entity_to_schema(res) for res in result]
    return lst_result