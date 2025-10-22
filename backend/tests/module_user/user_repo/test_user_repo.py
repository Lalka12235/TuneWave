from backend.tests.module_user.user_repo.conftest import get_user_data, create_table, get_user_repo
from app.models import User


def test_get_user_by_email(get_user_data, get_user_repo):
    """Проверяет получение пользователя по email."""
    created_user: User = get_user_repo.create_user(get_user_data)
    email = get_user_data["email"]

    fetched_user: User = get_user_repo.get_user_by_email(email)

    assert fetched_user is not None
    assert fetched_user.email == email


def test_get_user_by_id(get_user_data, get_user_repo):
    """Проверяет получение пользователя по ID."""
    created_user: User = get_user_repo.create_user(get_user_data)

    fetched_user: User = get_user_repo.get_user_by_id(created_user.id)

    assert fetched_user is not None
    assert fetched_user.id == created_user.id


def test_get_user_by_google_id(get_user_data, get_user_repo):
    """Проверяет получение пользователя по Google ID."""
    created_user: User = get_user_repo.create_user(get_user_data)

    fetched_user: User = get_user_repo.get_user_by_google_id(created_user.google_id)

    assert fetched_user is not None
    assert fetched_user.google_id == created_user.google_id


def test_get_user_by_spotify_id(get_user_data, get_user_repo):
    """Проверяет получение пользователя по Spotify ID."""
    created_user: User = get_user_repo.create_user(get_user_data)

    fetched_user: User = get_user_repo.get_user_by_spotify_id(created_user.spotify_id)

    assert fetched_user is not None
    assert fetched_user.spotify_id == created_user.spotify_id


def test_create_user(get_user_data, create_table, get_user_repo):
    """Проверяет создание нового пользователя."""
    user: User = get_user_repo.create_user(get_user_data)

    assert user is not None
    assert user.username == get_user_data["username"]
    assert user.email == get_user_data["email"]


def test_update_user(get_user_data, create_table, get_user_repo):
    """Проверяет обновление данных пользователя."""
    created_user: User = get_user_repo.create_user(get_user_data)
    update_data = {"username": "aspirin2"}

    updated_user: User = get_user_repo.update_user(created_user, update_data)

    assert updated_user is not None
    assert updated_user.username == "aspirin2"


def test_hard_delete_user(get_user_data, create_table, get_user_repo):
    """Проверяет жесткое удаление пользователя."""
    created_user: User = get_user_repo.create_user(get_user_data)

    deleted: bool = get_user_repo.hard_delete_user(created_user.id)

    assert deleted is True
