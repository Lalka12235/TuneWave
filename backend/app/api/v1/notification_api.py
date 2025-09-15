from fastapi import APIRouter, Depends, Path, status, Query
from sqlalchemy.orm import Session
import uuid
from typing import Annotated
from app.config.session import get_db
from app.auth.auth import get_current_user
from app.models import User 
from app.schemas.notification_schemas import NotificationResponse 
from app.services.notification_service import NotificationService
from fastapi_limiter.depends import RateLimiter


notification = APIRouter(
    tags=['Notifications'],
    prefix='/notifications'
)

db_dependencies = Annotated[Session,Depends(get_db)]
user_dependencies = Annotated[User,Depends(get_current_user)]


@notification.get(
    '/my',
    response_model=list[NotificationResponse],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(RateLimiter(times=10, seconds=60))]
)
async def get_my_notifications(
    db:db_dependencies,
    user:user_dependencies,
    limit: Annotated[int, Query(ge=1, le=100, description="Максимальное количество уведомлений для возврата.")] = 10,
    offset: Annotated[int, Query(ge=0, description="Смещение для пагинации.")] = 0,
) -> list[NotificationResponse]:
    """
    Получает список уведомлений для текущего аутентифицированного пользователя.

    Args:
        db (Session): Сессия базы данных.
        current_user (User): Текущий аутентифицированный пользователь.
        is_read (Optional[bool]): Фильтр по статусу прочитанности (True - только прочитанные, False - только непрочитанные, None - все).
        limit (int): Максимальное количество уведомлений для возврата.
        offset (int): Смещение для пагинации.

    Returns:
        List[NotificationResponse]: Список объектов NotificationResponse.
    """
    return NotificationService.get_user_notifications(
        db, user.id,limit=limit, offset=offset
    )


@notification.put(
    '/{notification_id}/mark-read',
    response_model=NotificationResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(RateLimiter(times=5, seconds=60))]
)
async def mark_notification_as_read(
    notification_id: Annotated[uuid.UUID,Path(...,description="ID уведомления, которое нужно отметить как прочитанное.")],
    db: db_dependencies,
    user: user_dependencies,
) -> NotificationResponse:
    """
    Отмечает конкретное уведомление как прочитанное.

    Args:
        notification_id (uuid.UUID): ID уведомления.
        db (Session): Сессия базы данных.
        current_user (User): Текущий аутентифицированный пользователь (владелец уведомления).

    Returns:
        NotificationResponse: Детали обновленного уведомления.
    """
    return NotificationService.mark_notification_as_read(
        db, notification_id, user.id
    )


@notification.delete(
    '/{notification_id}',
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(RateLimiter(times=5, seconds=60))]
)
async def delete_notifications(
    notification_id: Annotated[uuid.UUID,Path(...,description="ID уведомления, которое нужно отметить как прочитанное.")],
    db: db_dependencies,
    user: user_dependencies,
) -> dict[str,str]:
    """
    Удаляет конкретное уведомление.

    Args:
        notification_id (uuid.UUID): ID уведомления.
        db (Session): Сессия базы данных.
        current_user (User): Текущий аутентифицированный пользователь (владелец уведомления).

    Returns:
        dict[str, str]: Сообщение об успешном удалении.
    """
    return NotificationService.delete_notification(
        db, notification_id, user.id
    )