import uuid
from app.domain.enum import NotificationType
from app.infrastructure.db.gateway.notification_gateway import NotificationGateway

def test_get_notification_by_id(notification_repo: NotificationGateway, user_data1: dict):
    notification = notification_repo.add_notification(
        user_id=user_data1['id'],
        notification_type=NotificationType.FRIEND_REQUEST,
        message="Test notification"
    )

    found_notification = notification_repo.get_notification_by_id(notification.id)
    
    assert found_notification is not None
    assert found_notification.id == notification.id
    assert found_notification.user_id == user_data1['id']
    assert found_notification.message == "Test notification"

def test_get_user_notification(notification_repo: NotificationGateway, user_data1: dict):
    for i in range(15):
        notification_repo.add_notification(
            user_id=user_data1['id'],
            notification_type=NotificationType.FRIEND_REQUEST,
            message=f"Test notification {i}"
        )

    notifications = notification_repo.get_user_notification(
        user_id=user_data1['id'],
        limit=10,
        offset=0
    )
    
    assert len(notifications) == 10
    assert all(notif.user_id == user_data1['id'] for notif in notifications)

    next_notifications = notification_repo.get_user_notification(
        user_id=user_data1['id'],
        limit=10,
        offset=10
    )
    
    assert len(next_notifications) == 5

def test_add_notification(notification_repo: NotificationGateway, user_data1: dict, user_data2: dict):
    room_id = uuid.uuid4()
    
    notification = notification_repo.add_notification(
        user_id=user_data1['id'],
        notification_type=NotificationType.ROOM_INVITED,
        message="Room invite test",
        sender_id=user_data2['id'],
        room_id=room_id
    )
    
    assert notification is not None
    assert notification.user_id == user_data1['id']
    assert notification.notification_type == NotificationType.ROOM_INVITED
    assert notification.message == "Room invite test"
    assert notification.sender_id == user_data2['id']
    assert notification.room_id == room_id
    assert notification.is_read is False

def test_mark_notification_as_read(notification_repo: NotificationGateway, user_data1: dict):
    notification = notification_repo.add_notification(
        user_id=user_data1['id'],
        notification_type=NotificationType.FRIEND_REQUEST,
        message="Test notification"
    )

    updated = notification_repo.mark_notification_as_read(notification.id)
    
    assert updated is not None
    assert updated is True

    found = notification_repo.get_notification_by_id(notification.id)
    assert found.is_read is True

def test_delete_notification(notification_repo: NotificationGateway, user_data1: dict):
    notification = notification_repo.add_notification(
        user_id=user_data1['id'],
        notification_type=NotificationType.FRIEND_REQUEST,
        message="Test notification"
    )

    result = notification_repo.delete_notification(notification.id)
    
    assert result is True
    
    found = notification_repo.get_notification_by_id(notification.id)
    assert found is None

def test_nonexistent_notification(notification_repo: NotificationGateway):
    fake_id = uuid.uuid4()
    
    found = notification_repo.get_notification_by_id(fake_id)
    assert found is None
    
    updated = notification_repo.mark_notification_as_read(fake_id)
    assert updated is False
    
    result = notification_repo.delete_notification(fake_id)
    assert result is False

def test_add_notification_with_related_object(notification_repo: NotificationGateway, user_data1: dict):
    related_id = uuid.uuid4()
    
    notification = notification_repo.add_notification(
        user_id=user_data1['id'],
        notification_type=NotificationType.FRIEND_REQUEST,
        message="Test with related object",
        related_object_id=related_id
    )
    
    assert notification.related_object_id == related_id
    
    found = notification_repo.get_notification_by_id(notification.id)
    assert found.related_object_id == related_id