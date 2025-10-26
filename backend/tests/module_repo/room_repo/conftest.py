import pytest
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from app.models import Base
from app.repositories.room_repo import RoomRepository
from sqlalchemy.orm import Session
from typing import Generator,Any
from app.schemas.room_schemas import RoomCreate

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
def room_repo(db_session: Session) -> RoomRepository:
    """
    Предоставляет экземпляр UserRepository, используя сессию, 
    предоставленную фикстурой db_session.
    """
    repo = RoomRepository(db_session)
    return repo

@pytest.fixture(scope="function")
def room_data() -> dict[str,Any]:
    return {
        'name':'aspirin',
        'max_members': 2,
        'is_private': False,
    }