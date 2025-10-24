from tests.module_repo.track_repo.conftest import create_table, get_track_repo,get_track_data
from app.models import Track
import uuid


def test_get_track_by_id(create_table,get_track_repo,get_track_data):
    created = get_track_repo.create_track(get_track_data)

    fetched = get_track_repo.get_track_by_id(created.id)

    assert fetched is not None
    assert fetched.id == created.id
    assert fetched.title == get_track_data.title

def test_get_track_by_id_invalid_id(create_table,get_track_repo,get_track_data):
    result = get_track_repo.get_track_by_id(uuid.UUID('12345678-1234-5678-1234-567812345678'))

    assert result is None

def test_get_track_by_spotify_id(create_table,get_track_repo,get_track_data):
    created: Track = get_track_repo.create_track(get_track_data)

    fetched = get_track_repo.get_track_by_spotify_id(get_track_data.spotify_id)

    assert fetched is not None
    assert fetched.title == 'string'


def test_create_track(create_table,get_track_repo,get_track_data):
    track: Track = get_track_repo.create_track(get_track_data)

    assert track is not None
    assert track.title == get_track_data.title
    assert track.spotify_id == get_track_data.spotify_id
    assert isinstance(track.id, uuid.UUID)
    assert track.created_at is not None


def test_delete_track(create_table,get_track_repo,get_track_data):
    created: Track = get_track_repo.create_track(get_track_data)
    assert get_track_repo.get_track_by_id(created.id) is not None

    deleted = get_track_repo.delete_track(created.id)
    assert deleted == True
    assert get_track_repo.get_track_by_id(created.id) is None


def test_delete_track_not_exists(create_table,get_track_repo,get_track_data):
    deleted = get_track_repo.delete_track(uuid.UUID('12345678-1234-5678-1234-567812345678'))

    assert deleted is False