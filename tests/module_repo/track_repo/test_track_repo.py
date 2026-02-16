from app.infrastructure.db.models import Track
import uuid


def test_get_track_by_id(track_repo,track_data):
    created: Track = track_repo.create_track(track_data)


    fetched: Track = track_repo.get_track_by_id(created.id)

    assert fetched is not None
    assert fetched.id == created.id
    assert fetched.title == track_data['title']

def test_get_track_by_id_invalid_id(track_repo):
    result = track_repo.get_track_by_id(uuid.UUID('12345678-1234-5678-1234-567812345678'))

    assert result is None

def test_get_track_by_spotify_id(track_repo,track_data):
    track_repo.create_track(track_data)

    fetched: Track = track_repo.get_track_by_spotify_id(track_data['spotify_id'])

    assert fetched is not None
    assert fetched.title == 'string'


def test_create_track(track_repo,track_data):
    track: Track = track_repo.create_track(track_data)

    assert track is not None
    assert track.title == track_data['title']
    assert track.spotify_id == track_data['spotify_id']
    assert isinstance(track.id, uuid.UUID)
    assert track.created_at is not None


def test_delete_track(track_repo,track_data):
    created: Track = track_repo.create_track(track_data)
    assert track_repo.get_track_by_id(created.id) is not None

    deleted: bool = track_repo.delete_track(created.id)
    assert deleted
    assert track_repo.get_track_by_id(created.id) is None


def test_delete_track_not_exists(track_repo):
    deleted: bool = track_repo.delete_track(uuid.UUID('12345678-1234-5678-1234-567812345678'))

    assert deleted is False