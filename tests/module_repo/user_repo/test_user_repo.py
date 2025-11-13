from app.models import User
from app.repositories.user_repo import UserRepository
from app.schemas.user_schemas import UserCreate

def test_get_user_by_email(user_data: UserCreate, user_repo: UserRepository):
    """Проверяет получение пользователя по email."""
    user_repo.create_user(user_data)
    email = user_data["email"]

    fetched_user: User = user_repo.get_user_by_email(email)

    assert fetched_user is not None
    assert fetched_user.email == email


def test_get_user_by_id(user_data: UserCreate, user_repo: UserRepository):
    """Проверяет получение пользователя по ID."""
    created_user: User = user_repo.create_user(user_data)

    fetched_user: User = user_repo.get_user_by_id(created_user.id)

    assert fetched_user is not None
    assert fetched_user.id == created_user.id


def test_get_user_by_google_id(user_data: UserCreate, user_repo: UserRepository):
    """Проверяет получение пользователя по Google ID."""
    created_user: User = user_repo.create_user(user_data)

    fetched_user: User = user_repo.get_user_by_google_id(created_user.google_id)

    assert fetched_user is not None
    assert fetched_user.google_id == created_user.google_id


def test_get_user_by_spotify_id(user_data: UserCreate, user_repo: UserRepository):
    """Проверяет получение пользователя по Spotify ID."""
    created_user: User = user_repo.create_user(user_data)

    fetched_user: User = user_repo.get_user_by_spotify_id(created_user.spotify_id)

    assert fetched_user is not None
    assert fetched_user.spotify_id == created_user.spotify_id


def test_create_user(user_data: UserCreate, create_table, user_repo: UserRepository):
    """Проверяет создание нового пользователя."""
    user: User = user_repo.create_user(user_data)

    assert user is not None
    assert user.username == user_data["username"]
    assert user.email == user_data["email"]


def test_update_user(user_data: UserCreate, create_table, user_repo: UserRepository):
    """Проверяет обновление данных пользователя."""
    created_user: User = user_repo.create_user(user_data)
    update_data = {"username": "aspirin2"}

    updated_user: User = user_repo.update_user(created_user, update_data)

    assert updated_user is not None
    assert updated_user.username == "aspirin2"


def test_hard_delete_user(user_data: UserCreate, create_table, user_repo: UserRepository):
    """Проверяет жесткое удаление пользователя."""
    created_user: User = user_repo.create_user(user_data)

    deleted: bool = user_repo.hard_delete_user(created_user.id)

    assert deleted is True
