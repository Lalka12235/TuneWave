import uuid

from app.domain.entity import TrackEntity
from app.domain.interfaces.favorite_track_gateway import FavoriteTrackGateway


class ReadFavoriteTrack:
    def __init__(self,ft_repo: FavoriteTrackGateway):
        self.ft_repo = ft_repo

    def get_user_favorite_tracks(self, user_id: uuid.UUID) -> list[TrackEntity]:
        """
        Получает список всех любимых треков для указанного пользователя.
        """
        favorite_tracks = self.ft_repo.get_favorite_tracks( user_id)

        if not favorite_tracks:
            return []

        return [ft for ft in favorite_tracks]