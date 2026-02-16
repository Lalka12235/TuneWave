from app.infrastructure.db.gateway.favorite_track_gateway import FavoriteTrackGateway
from app.infrastructure.db.gateway.user_gateway import UserGateway
from app.infrastructure.db.gateway.track_gateway import TrackGateway
from app.presentation.schemas.track_schemas import TrackCreate
from app.infrastructure.db.models import User, FavoriteTrack, Track
from app.presentation.schemas.user_schemas import UserCreate


def test_get_favorite_track(
    create_table,
    favorite_track_repo: FavoriteTrackGateway,
    user_repo: UserGateway,
    user_data: UserCreate,
    track_repo: TrackGateway,
    track_data: TrackCreate,
):
    created_user: User = user_repo.create_user(user_data)
    assert created_user is not None
    created_track: Track = track_repo.create_track(track_data)
    assert created_track is not None

    favorite_track_repo.add_favorite_track(created_user.id,created_track.id)

    fetched: list[FavoriteTrack] = favorite_track_repo.get_favorite_tracks(
        created_user.id
    )
    assert fetched is not None
    assert len(fetched) > 0


def test_add_favorite_track(
    create_table,
    favorite_track_repo: FavoriteTrackGateway,
    user_repo: UserGateway,
    user_data: UserCreate,
    track_repo: TrackGateway,
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
    favorite_track_repo: FavoriteTrackGateway,
    user_repo: UserGateway,
    user_data: UserCreate,
    track_repo: TrackGateway,
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
    assert success_delete


def test_is_favorite_track(
    create_table,
    favorite_track_repo: FavoriteTrackGateway,
    user_repo: UserGateway,
    user_data: UserCreate,
    track_repo: TrackGateway,
    track_data: TrackCreate,
):
    created_user: User = user_repo.create_user(user_data)
    assert created_user is not None
    created_track: Track = track_repo.create_track(track_data)
    assert created_track is not None

    new_favorite_track: FavoriteTrack = favorite_track_repo.add_favorite_track(created_user.id,created_track.id)
    
    assert new_favorite_track is not None

    fetched: bool = favorite_track_repo.is_favorite_track(created_user.id,created_track.id)

    assert fetched
