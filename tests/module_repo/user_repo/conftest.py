import pytest
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from app.infrastructure.db.models import Base
from app.infrastructure.db.gateway.user_gateway import SAUserGateway
from sqlalchemy.orm import Session
from typing import Generator
import uuid

db_url = "sqlite:///:memory:"

engine = create_engine(url=db_url, echo=False)

TestSession = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)



@pytest.fixture(scope="function", autouse=True)
def create_table() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


@pytest.fixture(scope="function")
def db_session() -> Generator[Session,None,None]:
    """
    Предоставляет сессию БД. Выполняет commit при успехе и rollback при ошибке.
    """
    db = TestSession()
    try:
        yield db
        db.commit() 
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

@pytest.fixture(scope="function")
def user_repo(db_session: Session) -> SAUserGateway:
    """
    Предоставляет экземпляр UserRepository, используя сессию, 
    предоставленную фикстурой db_session.
    """
    repo = SAUserGateway(db_session)
    return repo


@pytest.fixture(scope="function")
def user_data() -> dict[str,str]:
    return {
        'id': uuid.UUID('5f4a3141-7160-454d-a9c0-1442887d4a7c'),
        'username': 'aspirin',
        'email': 'example@gmail.com',
        'is_email_verified': True,
        'google_id': '108973783984480761318',
        'google_image_url': 'https://lh3.googleusercontent.com/',
        'spoitfy_id': None,
        'spotify_profile_url': None,
        'spotify_image_url': None,
        'spotify_access_token': None,
        'spotify_refresh_token': None,
        'spotify_token_expires': None,
        'google_access_token': 'CgERyARtjw0206',
        'google_refresh_token': '1/c',
        'google_token_expires': 1755947584,
        'avatar_url': None,
        'bio': None
    }

