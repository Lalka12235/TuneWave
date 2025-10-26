from tests.module_repo.favorite_track_repo.conftest import (
    create_table,
    favorite_track_repo,
)
from tests.module_repo.user_repo.conftest import user_repo, user_data
from tests.module_repo.track_repo.conftest import track_repo, track_data
from app.repositories.favorite_track_repo import FavoriteTrackRepository
from app.repositories.user_repo import UserRepository
from app.repositories.track_repo import TrackRepository
from app.schemas.track_schemas import TrackCreate
from app.models import User, FavoriteTrack, Track
from app.schemas.user_schemas import UserCreate


def test_get_favorite_track(
    create_table,
    favorite_track_repo: FavoriteTrackRepository,
    user_repo: UserRepository,
    user_data: UserCreate,
    track_repo: TrackRepository,
    track_data: TrackCreate,
):
    created_user: User = user_repo.create_user(user_data)
    assert created_user is not None
    created_track: Track = track_repo.create_track(track_data)
    assert created_track is not None

    new_favorite_track: FavoriteTrack = favorite_track_repo.add_favorite_track(created_user.id,created_track.id)

    fetched: list[FavoriteTrack] = favorite_track_repo.get_favorite_tracks(
        created_user.id
    )
    assert fetched is not None
    assert len(fetched) > 0


def test_add_favorite_track(
    create_table,
    favorite_track_repo: FavoriteTrackRepository,
    user_repo: UserRepository,
    user_data: UserCreate,
    track_repo: TrackRepository,
    track_data: TrackCreate,
):
    created_user: User = user_repo.create_user(user_data)
    assert created_user is not None
    created_track: Track = track_repo.create_track(track_data)
    assert created_track is not None

    new_favorite_track: FavoriteTrack = favorite_track_repo.add_favorite_track(created_user.id,created_track.id)
    
    assert new_favorite_track is not None

    fetched: list[FavoriteTrack] = favorite_track_repo.get_favorite_tracks(
        created_user.id
    )
    assert fetched is not None
    assert len(fetched) > 0


def test_remove_favorite_track(
    create_table,
    favorite_track_repo: FavoriteTrackRepository,
    user_repo: UserRepository,
    user_data: UserCreate,
    track_repo: TrackRepository,
    track_data: TrackCreate,
):
    created_user: User = user_repo.create_user(user_data)
    assert created_user is not None
    created_track: Track = track_repo.create_track(track_data)
    assert created_track is not None

    new_favorite_track: FavoriteTrack = favorite_track_repo.add_favorite_track(created_user.id,created_track.id)
    
    assert new_favorite_track is not None

    fetched: list[FavoriteTrack] = favorite_track_repo.get_favorite_tracks(
        created_user.id
    )
    assert fetched is not None
    assert len(fetched) > 0

    success_delete: bool = favorite_track_repo.remove_favorite_track(created_user.id,created_track.id)
    assert success_delete == True


def test_is_favorite_track(
    create_table,
    favorite_track_repo: FavoriteTrackRepository,
    user_repo: UserRepository,
    user_data: UserCreate,
    track_repo: TrackRepository,
    track_data: TrackCreate,
):
    created_user: User = user_repo.create_user(user_data)
    assert created_user is not None
    created_track: Track = track_repo.create_track(track_data)
    assert created_track is not None

    new_favorite_track: FavoriteTrack = favorite_track_repo.add_favorite_track(created_user.id,created_track.id)
    
    assert new_favorite_track is not None

    fetched: bool = favorite_track_repo.is_favorite_track(created_user.id,created_track.id)

    assert fetched == True
