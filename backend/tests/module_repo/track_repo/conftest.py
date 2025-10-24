import pytest
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from app.models import Base
from app.repositories.track_repo import TrackRepository
from sqlalchemy.orm import Session
from typing import Generator,Any
import uuid
import datetime
from app.schemas.track_schemas import TrackCreate

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
def get_track_repo(db_session: Session) -> TrackRepository:
    """
    Предоставляет экземпляр UserRepository, используя сессию, 
    предоставленную фикстурой db_session.
    """
    repo = TrackRepository(db_session)
    return repo

@pytest.fixture(scope="function")
def get_track_data() -> TrackCreate:
    return TrackCreate(
        title='string',
        duration_ms=0,
        spotify_track_url='string',
        spotify_uri='string',
        spotify_id='string',
        artist_names=['string'],
        album_name='string',
        album_cover_url='string',
        is_playable=True,
    )