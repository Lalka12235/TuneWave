import pytest
from app.models import Base,User
from app.config.session import engine, SessionLocal
import uuid
from sqlalchemy.orm import Session
from app.utils import create_access_token

@pytest.fixture
def create_test_user(db_session: Session) -> User:
    """Создает и сохраняет тестового пользователя в БД."""
    test_user = User(
        id=uuid.uuid4(),
        username="TestUser",
        email="test_user@example.com",
        is_email_verified=True,
    )
    db_session.add(test_user)
    db_session.commit()
    db_session.refresh(test_user)
    return test_user

@pytest.fixture
def create_another_user(db_session: Session) -> User:
    """Создает и сохраняет другого тестового пользователя в БД."""
    another_user_id = uuid.uuid4()
    test_user = User(
        id=another_user_id,
        username="AnotherUser",
        email="another_user@example.com",
        is_email_verified=True,
    )
    db_session.add(test_user)
    db_session.commit()
    db_session.refresh(test_user)
    return test_user

@pytest.fixture
def get_jwt_token(create_test_user: User) -> str:
    """Генерирует JWT токен для тестового пользователя."""
    return create_access_token(payload={"sub": str(create_test_user.id)})

@pytest.fixture(scope="function", autouse=True)
def setup_test_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
