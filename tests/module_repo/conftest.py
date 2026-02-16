from typing import Any
import pytest
from app.domain.entity.track import TrackEntity
from app.infrastructure.db.gateway.room_gateway import SARoomGateway
from app.infrastructure.db.gateway.track_gateway import SATrackGateway
from app.infrastructure.db.gateway.user_gateway import SAUserGateway
from sqlalchemy.orm import Session
import uuid
from datetime import datetime



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
        'avatar_url': None,
        'bio': None
    }
    

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


@pytest.fixture(scope="function")
def user_data1() -> dict[str,str]:
    return {
        'id': uuid.UUID('5f4a3141-7160-454d-a9c0-1442887d4a7c'),
        'username': 'aspirin',
        'email': 'example@gmail.com',
        'is_email_verified': True,
        'google_id': '108973783984480761318',
        'google_image_url': 'https://lh3.googleusercontent.com/',
        'spotify_id': None,
        'spotify_profile_url': None,
        'spotify_image_url': None,
        'avatar_url': None,
        'bio': None
    }

@pytest.fixture(scope="function")
def user_data2() -> dict[str,str]:
    return {
        'id': uuid.UUID('5f4a3141-7160-454d-a9c0-2322887d4a7c'),
        'username': 'aspirin2',
        'email': 'example@gmail.com',
        'is_email_verified': True,
        'google_id': '108973783984480761318',
        'google_image_url': 'https://lh3.googleusercontent.com/',
        'spotify_id': None,
        'spotify_profile_url': None,
        'spotify_image_url': None,
        'avatar_url': None,
        'bio': None
    }
    
@pytest.fixture(scope="function")
def room_repo(db_session: Session) -> SARoomGateway:
    """
    Предоставляет экземпляр UserRepository, используя сессию, 
    предоставленную фикстурой db_session.
    """
    repo = SARoomGateway(db_session)
    return repo

@pytest.fixture(scope="function")
def room_data() -> dict[str,Any]:
    return {
        'name':'aspirin',
        'max_members': 2,
        'is_private': False,
    }