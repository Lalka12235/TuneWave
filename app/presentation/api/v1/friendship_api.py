import uuid
from typing import Annotated

from fastapi import APIRouter, Path, status

from app.domain.entity import UserEntity
from app.infrastructure.redis.redis_service import RedisService
from app.presentation.schemas.friendship_schemas import FriendshipRequestCreate, FriendshipResponse

from dishka.integrations.fastapi import DishkaRoute,FromDishka

from app.application.commands.friendship import ReadFriendship,SendFriendRequest,AcceptFriendRequest,DeleteFreidnship,DeclineFriendRequest

friendship = APIRouter(
    tags=['Friendship'],
    prefix='/friendships',
    route_class=DishkaRoute
)

user_dependencies = FromDishka[UserEntity]
redis_service = FromDishka[RedisService]



@friendship.post(
    '/send-request',
    response_model=FriendshipResponse,
    status_code=status.HTTP_201_CREATED,
)
async def send_friend_request(
    interactor: FromDishka[SendFriendRequest],
    request_data: FriendshipRequestCreate,
    user: user_dependencies,
) -> FriendshipResponse:
    """
    Отправляет запрос на дружбу указанному пользователю.
    """
    return await interactor.send_friend_request(user.id,request_data.accepter_id)


@friendship.put(
    '/{friendship_id}/accept',
    response_model=FriendshipResponse,
    status_code=status.HTTP_200_OK,
)
async def accept_friend_request(
   interactor: FromDishka[AcceptFriendRequest],
    friendship_id: Annotated[uuid.UUID,Path(..., description="ID запроса на дружбу для принятия.")],
    user: user_dependencies,
) -> FriendshipResponse:
    """
    Принимает ожидающий запрос на дружбу.
    """
    return await interactor.accept_friend_request(friendship_id,user.id)


@friendship.put(
    '/{friendship_id}/decline',
    response_model=FriendshipResponse,
    status_code=status.HTTP_200_OK,
)
async def decline_friend_request(
    interactor: FromDishka[DeclineFriendRequest],
    friendship_id: Annotated[uuid.UUID,Path(..., description="ID запроса на дружбу для отклонения.")],
    user: user_dependencies,
) -> FriendshipResponse:
    """
    Отклоняет ожидающий запрос на дружбу.
    """
    return await interactor.decline_friend_request(friendship_id,user.id)


@friendship.delete(
    "/{friendship_id}",
    status_code=status.HTTP_200_OK,
)
async def delete_friendship(
    interactor: FromDishka[DeleteFreidnship],
    friendship_id: Annotated[uuid.UUID, Path(..., description="ID записи о дружбе для удаления.")],
    current_user: user_dependencies,
) -> dict[str, str]:
    """
    Удаляет существующую запись о дружбе или отменяет ожидающий запрос.
    """
    return await interactor.delete_friendship(friendship_id,current_user.id)



@friendship.get(
    '/my-friends',
    response_model=list[FriendshipResponse],
    status_code=status.HTTP_200_OK,
)
async def get_my_friend(
    interactor: FromDishka[ReadFriendship],
    user: user_dependencies,
    redis_client: redis_service,
) -> list[FriendshipResponse]:
    """
    Получает список всех принятых друзей текущего аутентифицированного пользователя.
    """
    key = f'friendship:get_my_friend:{user.id}'
    async def fetch():
        return interactor.get_my_fridns(user.id)
    return await redis_client.get_or_set(key,fetch,300)

@friendship.get(
    '/my-send-requests',
    response_model=list[FriendshipResponse],
    status_code=status.HTTP_200_OK,
)
async def get_my_sent_requests(
    interactor: FromDishka[ReadFriendship],
    current_user: user_dependencies,
    redis_client: redis_service,
) -> list[FriendshipResponse]:
    """
    Получает список запросов на дружбу, отправленных текущим аутентифицированным пользователем,
    которые находятся в статусе PENDING.
    """
    key = f'friendship:get_my_sent_requests:{current_user.id}'
    async def fetch():
        return await interactor.get_my_sent_requests(current_user.id)
    return await redis_client.get_or_set(key,fetch,300)


@friendship.get(
    '/my-received-requests',
    response_model=list[FriendshipResponse],
    status_code=status.HTTP_200_OK,
)
async def get_my_received_requests(
    interactor: FromDishka[ReadFriendship],
    current_user: user_dependencies,
    redis_client: redis_service,
) -> list[FriendshipResponse]:
    """
    Получает список запросов на дружбу, полученных текущим аутентифицированным пользователем,
    которые находятся в статусе PENDING.
    """
    key = f'friendship:get_my_received_requests:{current_user.id}'
    async def fetch():
        return await interactor.get_my_received_requests(current_user.id)
    return await redis_client.get_or_set(key,fetch,300)