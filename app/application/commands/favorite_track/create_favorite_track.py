import uuid

from app.domain.entity import UserEntity,TrackEntity
from app.domain.interfaces.favorite_track_gateway import FavoriteTrackGateway
from app.domain.interfaces.track_gateway import TrackGateway
from app.infrastructure.external.spotify import SpotifyService,SpotifyPublicService #todo

from app.domain.exceptions.exception import ServerError
from app.domain.exceptions.favorite_track_exception import TrackNotFound,TrackInFavorite


class CreateTrackFavorite:
    def __init__(self,ft_repo: FavoriteTrackGateway,track_repo: TrackGateway):
        self.ft_repo = ft_repo
        self.track_repo = track_repo


    async def _get_or_create_track(self, spotify_id: str,current_user: UserEntity | None = None) -> TrackEntity:
        """
        Ищет трек в нашей базе данных по Spotify ID. Если не находит,
        получает информацию о треке из Spotify API и сохраняет его в нашей БД.
        """
        track = self.track_repo.get_track_by_spotify_id(spotify_id)
        if track:
            return track
        
        spotify_detail = ''
        if current_user:
            spotify_user_service = SpotifyService(current_user)
            spotify_detail = await spotify_user_service.search_track_by_spotify_id(spotify_id)

        if not spotify_detail:
                spotify_public_service = SpotifyPublicService()
                spotify_detail = await spotify_public_service.search_track_by_spotify_id(spotify_id)

        if not spotify_detail:
            raise TrackNotFound(
                detail=f"Трек с Spotify ID '{spotify_id}' не найден на Spotify."
            )
        try:
            new_track = self.track_repo.create_track(spotify_detail)
            return new_track
        except Exception as e:
            raise ServerError(
                detail=f"Ошибка сервера при обработке трека из Spotify: {e}"
            )


    async def add_favorite_track(self, user_id: uuid.UUID, spotify_id: str) -> TrackEntity:
        """
        Добавляет трек в список любимых треков пользователя.
        """
        track = await self._get_or_create_track(spotify_id)

        is_favorite = self.ft_repo.is_favorite_track( user_id, track.id)
        if is_favorite:
            raise TrackInFavorite()
        try:
            new_favorite_track = self.ft_repo.add_favorite_track( user_id, track.id)
            return new_favorite_track
        except Exception:
            raise ServerError(
                detail="Не удалось добавить любимый трек из-за внутренней ошибки сервера."
            )
