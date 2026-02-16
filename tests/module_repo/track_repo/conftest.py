import uuid
import pytest
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from app.domain.entity.track import TrackEntity
from app.infrastructure.db.models import Base
from app.infrastructure.db.gateway.track_gateway import SATrackGateway
from sqlalchemy.orm import Session
from typing import Generator
from datetime import datetime

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
def track_repo(db_session: Session) -> SATrackGateway:
    """
    Предоставляет экземпляр UserRepository, используя сессию, 
    предоставленную фикстурой db_session.
    """
    repo = SATrackGateway(db_session)
    return repo

@pytest.fixture(scope="function")
def track_data() -> dict:
    track_data = TrackEntity(
        id=uuid.UUID('12385678-1234-5678-1234-567812345678'),
        title='string',
        duration_ms=0,
        spotify_track_url='string',
        spotify_uri='string',
        spotify_id='string',
        artist_names=['string'],
        album_name='string',
        album_cover_url='string',
        is_playable=True,
        last_synced_at=datetime.now(),
        created_at=datetime.now()
    )
    track_data_dict = dict(
            spotify_id=track_data.spotify_id,
            spotify_uri=track_data.spotify_uri,
            title=track_data.title,
            artist_names=track_data.artist_names,
            album_name=track_data.album_name,
            album_cover_url=track_data.album_cover_url,
            duration_ms=track_data.duration_ms,
            is_playable=track_data.is_playable,
            spotify_track_url=track_data.spotify_track_url,
            last_synced_at=track_data.last_synced_at,
            created_at=track_data.created_at,
    )
    return track_data_dict
    