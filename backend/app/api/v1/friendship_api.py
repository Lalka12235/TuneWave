from fastapi import APIRouter,Depends,Path,status
from app.schemas.friendship_schemas import FriendshipResponse,FriendshipRequestCreate
import uuid
from sqlalchemy.orm import Session
from app.config.session import get_db
from app.auth.auth import get_current_user
from typing import Annotated
from app.models.user import User
from app.services.friendship_service import FriendshipService
from fastapi_limiter.depends import RateLimiter



friendship = APIRouter(
    tags=['Friendship'],
    prefix='/friendships'
)

db_dependencies = Annotated[Session,Depends(get_db)]
user_dependencies = Annotated[User,Depends(get_current_user)]


@friendship.post(
    '/send-request',
    response_model=FriendshipResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RateLimiter(times=5, seconds=60))]
)
async def send_friend_request(
    request_data: FriendshipRequestCreate,
    db: db_dependencies,
    user: user_dependencies,
) -> FriendshipResponse:
    """
    Отправляет запрос на дружбу указанному пользователю.

    Args:
        request_data (FriendshipRequestCreate): Данные запроса, содержащие ID пользователя-получателя.
        db (Session): Сессия базы данных.
        current_user (User): Текущий аутентифицированный пользователь (отправитель запроса).

    Returns:
        FriendshipResponse: Детали созданной записи о запросе на дружбу.
    """
    return await FriendshipService.send_friend_request(db,user.id,request_data.accepter_id)


@friendship.put(
    '/{friendship_id}/accept',
    response_model=FriendshipResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(RateLimiter(times=5, seconds=60))]
)
async def accept_friend_request(
    friendship_id: Annotated[uuid.UUID,Path(..., description="ID запроса на дружбу для принятия.")],
    db: db_dependencies,
    user: user_dependencies
) -> FriendshipResponse:
    """
    Принимает ожидающий запрос на дружбу.

    Args:
        friendship_id (uuid.UUID): ID записи о дружбе.
        db (Session): Сессия базы данных.
        current_user (User): Текущий аутентифицированный пользователь (получатель запроса).

    Returns:
        FriendshipResponse: Детали обновленной записи о дружбе.
    """
    return await FriendshipService.accept_friend_request(db,friendship_id,user.id)


@friendship.put(
    '/{friendship_id}/decline',
    response_model=FriendshipResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(RateLimiter(times=5, seconds=60))]
)
async def decline_friend_request(
    friendship_id: Annotated[uuid.UUID,Path(..., description="ID запроса на дружбу для отклонения.")],
    db: db_dependencies,
    user: user_dependencies
) -> FriendshipResponse:
    """
    Отклоняет ожидающий запрос на дружбу.

    Args:
        friendship_id (uuid.UUID): ID записи о дружбе.
        db (Session): Сессия базы данных.
        current_user (User): Текущий аутентифицированный пользователь (получатель запроса).

    Returns:
        FriendshipResponse: Детали обновленной записи о дружбе (статус DECLINED).
    """
    return await FriendshipService.decline_friend_request(db,friendship_id,user.id)


@friendship.delete(
    "/{friendship_id}",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(RateLimiter(times=5, seconds=60))]
)
async def delete_friendship(
    friendship_id: Annotated[uuid.UUID, Path(..., description="ID записи о дружбе для удаления.")],
    db: db_dependencies,
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
    # Вызываем метод сервиса для удаления дружбы
    return await FriendshipService.delete_friendship(db,friendship_id,current_user.id)



@friendship.get(
    '/my-friends',
    response_model=list[FriendshipResponse],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(RateLimiter(times=15, seconds=60))]
)
async def get_my_friend(
    db: db_dependencies,
    user: user_dependencies,
) -> list[FriendshipResponse]:
    """
    Получает список всех принятых друзей текущего аутентифицированного пользователя.

    Args:
        db (Session): Сессия базы данных.
        current_user (User): Текущий аутентифицированный пользователь.

    Returns:
        List[FriendshipResponse]: Список объектов FriendshipResponse со статусом ACCEPTED.
    """
    return FriendshipService.get_my_fridns(db,user.id)


@friendship.get(
    '/my-send-requests',
    response_model=list[FriendshipResponse],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(RateLimiter(times=15, seconds=60))]
)
async def get_my_sent_requests(
    db: db_dependencies,
    current_user: user_dependencies,
) -> list[FriendshipResponse]:
    """
    Получает список запросов на дружбу, отправленных текущим аутентифицированным пользователем,
    которые находятся в статусе PENDING.

    Args:
        db (Session): Сессия базы данных.
        current_user (User): Текущий аутентифицированный пользователь.

    Returns:
        List[FriendshipResponse]: Список объектов FriendshipResponse со статусом PENDING.
    """
    return FriendshipService.get_my_sent_requests(db,current_user.id)


@friendship.get(
    '/my-received-requests',
    response_model=list[FriendshipResponse],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(RateLimiter(times=15, seconds=60))]
)
async def get_my_received_requests(
    db: db_dependencies,
    current_user: user_dependencies,
) -> list[FriendshipResponse]:
    """
    Получает список запросов на дружбу, полученных текущим аутентифицированным пользователем,
    которые находятся в статусе PENDING.

    Args:
        db (Session): Сессия базы данных.
        current_user (User): Текущий аутентифицированный пользователь.

    Returns:
        List[FriendshipResponse]: Список объектов FriendshipResponse со статусом PENDING.
    """
    return FriendshipService.get_my_received_requests(db,current_user.id)