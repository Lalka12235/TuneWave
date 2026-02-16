import uuid
from app.infrastructure.db.models import User

def test_get_user_by_email(user_data, user_repo):
    """Проверяет получение пользователя по email."""
    user_repo.create_user(user_data)
    email = user_data["email"]

    fetched_user: User = user_repo.get_user_by_email(email)

    assert fetched_user is not None
    assert fetched_user.email == email


def test_get_user_by_id(user_data, user_repo):
    """Проверяет получение пользователя по ID."""
    created_user: User = user_repo.create_user(user_data)

    fetched_user: User = user_repo.get_user_by_id(created_user.id)

    assert fetched_user is not None
    assert fetched_user.id == created_user.id


def test_get_user_by_google_id(user_data, user_repo):
    """Проверяет получение пользователя по Google ID."""
    created_user: User = user_repo.create_user(user_data)

    fetched_user: User = user_repo.get_user_by_google_id(created_user.google_id)

    assert fetched_user is not None
    assert fetched_user.google_id == created_user.google_id


def test_get_user_by_spotify_id(user_data, user_repo):
    """Проверяет получение пользователя по Spotify ID."""
    created_user: User = user_repo.create_user(user_data)

    fetched_user: User = user_repo.get_user_by_spotify_id(created_user.spotify_id)

    assert fetched_user is not None
    assert fetched_user.spotify_id == created_user.spotify_id


def test_create_user(user_data, user_repo):
    """Проверяет создание нового пользователя."""
    user: User = user_repo.create_user(user_data)

    assert user is not None
    assert user.username == user_data["username"]
    assert user.email == user_data["email"]


def test_update_user(user_data, user_repo):
    created_user = user_repo.create_user(user_data)
    
    # Генерируем гарантированно новое имя
    new_username = f"updated_{uuid.uuid4().hex[:6]}"
    update_data = {"username": new_username}

    # ВАЖНО: передаем .id, так как метод ожидает uuid.UUID
    updated_user = user_repo.update_user(created_user.id, update_data)

    assert updated_user is not None
    assert updated_user.username == new_username


def test_hard_delete_user(user_data, user_repo):
    """Проверяет жесткое удаление пользователя."""
    created_user: User = user_repo.create_user(user_data)

    deleted: bool = user_repo.hard_delete_user(created_user.id)

    assert deleted is True
