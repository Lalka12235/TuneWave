import uuid

from app.domain.interfaces.favorite_track_gateway import FavoriteTrackGateway
from app.domain.interfaces.track_gateway import TrackGateway


from app.domain.exceptions.exception import ServerError
from app.domain.exceptions.favorite_track_exception import TrackNotFound


class DeleteFavoriteTrack:
    def __init__(self,ft_repo: FavoriteTrackGateway,track_repo: TrackGateway):
        self.ft_repo = ft_repo
        self.track_repo = track_repo


    def remove_favorite_track(self, user_id: uuid.UUID, spotify_id: str) -> dict[str, str]:
        """
        Удаляет трек из списка любимых треков пользователя.
        """

        track = self.track_repo.get_track_by_spotify_id( spotify_id)
        if not track:
            raise TrackNotFound(
                detail="Трек не найден в нашей базе данных."
            )

        is_favorite = self.ft_repo.is_favorite_track( user_id, track.id)
        if not is_favorite:
            raise TrackNotFound(
                detail="Этот трек не найден в вашем списке любимых."
            )
        try:
            removed_count = self.ft_repo.remove_favorite_track( user_id, track.id)

            if removed_count:
                return {
                    'action': 'remove favorite track',
                    'status': 'success',
                    'detail': f'Трек {spotify_id} успешно удален из избранного.',
                }
            else:
                raise ServerError(
                    detail="Не удалось удалить любимый трек."
                )
        except Exception:
            raise ServerError(
                detail="Не удалось удалить любимый трек из-за внутренней ошибки сервера."
            )