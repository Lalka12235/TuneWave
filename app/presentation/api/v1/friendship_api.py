import uuid
from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, Path, status

from app.domain.entity import UserEntity
from app.presentation.schemas.friendship_schemas import FriendshipRequestCreate, FriendshipResponse
from app.application.services.friendship_service import FriendshipService

from app.application.services.redis_service import RedisService
from app.presentation.dependencies import get_current_user

from dishka.integrations.fastapi import DishkaRoute,FromDishka,inject

friendship = APIRouter(
    tags=['Friendship'],
    prefix='/friendships',
    route_class=DishkaRoute
)

user_dependencies = Annotated[UserEntity,Depends(get_current_user)]
redis_service = FromDishka[RedisService]
friendship_service = FromDishka[FriendshipService]



@friendship.post(
    '/send-request',
    response_model=FriendshipResponse,
    status_code=status.HTTP_201_CREATED,
)
@inject
async def send_friend_request(
    friend_service: friendship_service,
    request_data: FriendshipRequestCreate,
    user: user_dependencies,
) -> FriendshipResponse:
    """
    Отправляет запрос на дружбу указанному пользователю.

    Args:
        request_data (FriendshipRequestCreate): Данные запроса, содержащие ID пользователя-получателя.
        current_user (User): Текущий аутентифицированный пользователь (отправитель запроса).

    Returns:
        FriendshipResponse: Детали созданной записи о запросе на дружбу.
    """
    return await friend_service.send_friend_request(user.id,request_data.accepter_id)


@friendship.put(
    '/{friendship_id}/accept',
    response_model=FriendshipResponse,
    status_code=status.HTTP_200_OK,
)
@inject
async def accept_friend_request(
    friend_service: friendship_service,
    friendship_id: Annotated[uuid.UUID,Path(..., description="ID запроса на дружбу для принятия.")],
    user: user_dependencies,
) -> FriendshipResponse:
    """
    Принимает ожидающий запрос на дружбу.

    Args:
        friendship_id (uuid.UUID): ID записи о дружбе.
        current_user (User): Текущий аутентифицированный пользователь (получатель запроса).

    Returns:
        FriendshipResponse: Детали обновленной записи о дружбе.
    """
    return await friend_service.accept_friend_request(friendship_id,user.id)


@friendship.put(
    '/{friendship_id}/decline',
    response_model=FriendshipResponse,
    status_code=status.HTTP_200_OK,
)
@inject
async def decline_friend_request(
    friend_service: friendship_service,
    friendship_id: Annotated[uuid.UUID,Path(..., description="ID запроса на дружбу для отклонения.")],
    user: user_dependencies,
) -> FriendshipResponse:
    """
    Отклоняет ожидающий запрос на дружбу.

    Args:
        friendship_id (uuid.UUID): ID записи о дружбе.
        current_user (User): Текущий аутентифицированный пользователь (получатель запроса).

    Returns:
        FriendshipResponse: Детали обновленной записи о дружбе (статус DECLINED).
    """
    return await friend_service.decline_friend_request(friendship_id,user.id)


@friendship.delete(
    "/{friendship_id}",
    status_code=status.HTTP_200_OK,
)
@inject
async def delete_friendship(
    friend_service: friendship_service,
    friendship_id: Annotated[uuid.UUID, Path(..., description="ID записи о дружбе для удаления.")],
    current_user: user_dependencies,
) -> dict[str, str]:
    """
    Удаляет существующую запись о дружбе или отменяет ожидающий запрос.

    Args:
        friendship_id (uuid.UUID): ID записи о дружбе.
        db (Session): Сессия базы данных.
        current_user (User): Текущий аутентифицированный пользователь (один из участников дружбы).

    Returns:
        dict[str, str]: Сообщение об успешном удалении.
    """
    return await friend_service.delete_friendship(friendship_id,current_user.id)



@friendship.get(
    '/my-friends',
    response_model=list[FriendshipResponse],
    status_code=status.HTTP_200_OK,
)
@inject
async def get_my_friend(
    friend_service: friendship_service,
    user: user_dependencies,
    redis_client: redis_service,
) -> list[FriendshipResponse]:
    """
    Получает список всех принятых друзей текущего аутентифицированного пользователя.

    Returns:
        List[FriendshipResponse]: Список объектов FriendshipResponse со статусом ACCEPTED.
    """
    key = f'friendship:get_my_friend:{user.id}'
    async def fetch():
        return friend_service.get_my_fridns(user.id)
    return await redis_client.get_or_set(key,fetch,300)

@friendship.get(
    '/my-send-requests',
    response_model=list[FriendshipResponse],
    status_code=status.HTTP_200_OK,
)
@inject
async def get_my_sent_requests(
    friend_service: friendship_service,
    current_user: user_dependencies,
    redis_client: redis_service,
) -> list[FriendshipResponse]:
    """
    Получает список запросов на дружбу, отправленных текущим аутентифицированным пользователем,
    которые находятся в статусе PENDING.

    Returns:
        List[FriendshipResponse]: Список объектов FriendshipResponse со статусом PENDING.
    """
    key = f'friendship:get_my_sent_requests:{current_user.id}'
    async def fetch():
        return await friend_service.get_my_sent_requests(current_user.id)
    return await redis_client.get_or_set(key,fetch,300)


@friendship.get(
    '/my-received-requests',
    response_model=list[FriendshipResponse],
    status_code=status.HTTP_200_OK,
)
@inject
async def get_my_received_requests(
    friend_service: friendship_service,
    current_user: user_dependencies,
    redis_client: redis_service,
) -> list[FriendshipResponse]:
    """
    Получает список запросов на дружбу, полученных текущим аутентифицированным пользователем,
    которые находятся в статусе PENDING.

    Returns:
        List[FriendshipResponse]: Список объектов FriendshipResponse со статусом PENDING.
    """
    key = f'friendship:get_my_received_requests:{current_user.id}'
    async def fetch():
        return await friend_service.get_my_received_requests(current_user.id)
    return await redis_client.get_or_set(key,fetch,300)