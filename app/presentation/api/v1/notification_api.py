import uuid
from typing import Annotated

from fastapi import APIRouter, Path, Query, status

from app.domain.entity import UserEntity,NotificationEntity
from app.presentation.schemas.notification_schemas import NotificationResponse

from dishka.integrations.fastapi import DishkaRoute,FromDishka
from app.application.commands.notification import ReadNotification,DeleteNotification,MarkReadNotification

notification = APIRouter(
    tags=['Notifications'],
    prefix='/notifications',
    route_class=DishkaRoute
)

user_dependencies = FromDishka[UserEntity]

def convert_entity_to_schema(entity: NotificationEntity) -> NotificationResponse:
    return NotificationResponse(
        id=entity.id,
        user_id=entity.user_id,
        #sender=entity.sender,
        room_id=entity.room_id,
        notification_type=entity.notification_type,
        message=entity.message,
        is_read=entity.is_read,
        created_at=entity.created_at
    )

@notification.get(
    '/my',
    response_model=list[NotificationResponse],
    status_code=status.HTTP_200_OK,
)
async def get_my_notifications(
    user:user_dependencies,
    interactor: FromDishka[ReadNotification],
    limit: Annotated[int, Query(ge=1, le=100, description="Максимальное количество уведомлений для возврата.")] = 10,
    offset: Annotated[int, Query(ge=0, description="Смещение для пагинации.")] = 0,
) -> list[NotificationResponse]:
    """
    Получает список уведомлений для текущего аутентифицированного пользователя.
    """
    result = interactor.get_user_notifications(
        user.id,limit=limit, offset=offset
    )
    return [convert_entity_to_schema(res) for res in result]

@notification.put(
    '/{notification_id}/mark-read',
    response_model=NotificationResponse,
    status_code=status.HTTP_200_OK,
)
async def mark_notification_as_read(
    interactor: FromDishka[MarkReadNotification],
    notification_id: Annotated[uuid.UUID,Path(...,description="ID уведомления, которое нужно отметить как прочитанное.")],
    user: user_dependencies,
) -> NotificationResponse:
    """
    Отмечает конкретное уведомление как прочитанное.
    """
    result = interactor.mark_notification_as_read(
        notification_id, user.id
    )
    return convert_entity_to_schema(result)


@notification.delete(
    '/{notification_id}',
    status_code=status.HTTP_200_OK,
)
async def delete_notifications(
    interactor: FromDishka[DeleteNotification],
    notification_id: Annotated[uuid.UUID,Path(...,description="ID уведомления, которое нужно отметить как прочитанное.")],
    user: user_dependencies,
) -> dict[str,str]:
    """
    Удаляет конкретное уведомление.
    """
    return interactor.delete_notification(
        notification_id, user.id
    )