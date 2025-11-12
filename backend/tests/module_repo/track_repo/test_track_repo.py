from app.models import Track
from app.repositories.track_repo import TrackRepository
from app.schemas.track_schemas import TrackCreate
import uuid


def test_get_track_by_id(create_table,track_repo: TrackRepository,track_data: TrackCreate):
    created: Track = track_repo.create_track(track_data)

    fetched: Track = track_repo.get_track_by_id(created.id)

    assert fetched is not None
    assert fetched.id == created.id
    assert fetched.title == track_data.title

def test_get_track_by_id_invalid_id(create_table,track_repo: TrackRepository,track_data: TrackCreate):
    result: None = track_repo.get_track_by_id(uuid.UUID('12345678-1234-5678-1234-567812345678'))

    assert result is None

def test_get_track_by_spotify_id(create_table,track_repo: TrackRepository,track_data: TrackCreate):
    track_repo.create_track(track_data)

    fetched: Track = track_repo.get_track_by_spotify_id(track_data.spotify_id)

    assert fetched is not None
    assert fetched.title == 'string'


def test_create_track(create_table,track_repo: TrackRepository,track_data: TrackCreate):
    track: Track = track_repo.create_track(track_data)

    assert track is not None
    assert track.title == track_data.title
    assert track.spotify_id == track_data.spotify_id
    assert isinstance(track.id, uuid.UUID)
    assert track.created_at is not None


def test_delete_track(create_table,track_repo: TrackRepository,track_data: TrackCreate):
    created: Track = track_repo.create_track(track_data)
    assert track_repo.get_track_by_id(created.id) is not None

    deleted: bool = track_repo.delete_track(created.id)
    assert deleted
    assert track_repo.get_track_by_id(created.id) is None


def test_delete_track_not_exists(create_table,track_repo: TrackRepository,track_data: TrackCreate):
    deleted: bool = track_repo.delete_track(uuid.UUID('12345678-1234-5678-1234-567812345678'))

    assert deleted is False