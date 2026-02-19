import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, status

from app.domain.entity import UserEntity
from app.presentation.schemas.notification_schemas import NotificationResponse
from app.application.services.notification_service import NotificationService
from app.presentation.dependencies import get_current_user

from dishka.integrations.fastapi import DishkaRoute,FromDishka,inject

notification = APIRouter(
    tags=['Notifications'],
    prefix='/notifications',
    route_class=DishkaRoute
)

user_dependencies = Annotated[UserEntity,Depends(get_current_user)]
notify_service = FromDishka[NotificationService]


@notification.get(
    '/my',
    response_model=list[NotificationResponse],
    status_code=status.HTTP_200_OK,
)
@inject
async def get_my_notifications(
    user:user_dependencies,
    notify_service: notify_service,
    limit: Annotated[int, Query(ge=1, le=100, description="Максимальное количество уведомлений для возврата.")] = 10,
    offset: Annotated[int, Query(ge=0, description="Смещение для пагинации.")] = 0,
) -> list[NotificationResponse]:
    """
    Получает список уведомлений для текущего аутентифицированного пользователя.

    Args:
        current_user (User): Текущий аутентифицированный пользователь.
        limit (int): Максимальное количество уведомлений для возврата.
        offset (int): Смещение для пагинации.

    Returns:
        List[NotificationResponse]: Список объектов NotificationResponse.
    """
    return notify_service.get_user_notifications(
        user.id,limit=limit, offset=offset
    )


@notification.put(
    '/{notification_id}/mark-read',
    response_model=NotificationResponse,
    status_code=status.HTTP_200_OK,
)
@inject
async def mark_notification_as_read(
    notify_service: notify_service,
    notification_id: Annotated[uuid.UUID,Path(...,description="ID уведомления, которое нужно отметить как прочитанное.")],
    user: user_dependencies,
) -> NotificationResponse:
    """
    Отмечает конкретное уведомление как прочитанное.

    Args:
        notification_id (uuid.UUID): ID уведомления.
        current_user (User): Текущий аутентифицированный пользователь (владелец уведомления).

    Returns:
        NotificationResponse: Детали обновленного уведомления.
    """
    return notify_service.mark_notification_as_read(
        notification_id, user.id
    )


@notification.delete(
    '/{notification_id}',
    status_code=status.HTTP_200_OK,
)
@inject
async def delete_notifications(
    notify_service: notify_service,
    notification_id: Annotated[uuid.UUID,Path(...,description="ID уведомления, которое нужно отметить как прочитанное.")],
    user: user_dependencies,
) -> dict[str,str]:
    """
    Удаляет конкретное уведомление.

    Args:
        notification_id (uuid.UUID): ID уведомления.
        current_user (User): Текущий аутентифицированный пользователь (владелец уведомления).

    Returns:
        dict[str, str]: Сообщение об успешном удалении.
    """
    return notify_service.delete_notification(
        notification_id, user.id
    )