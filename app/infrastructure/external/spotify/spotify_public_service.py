import time

import httpx

from app.config.settings import settings
from app.presentation.schemas.spotify_schemas import (
    SpotifyPlaylistsSearchPaging,
    SpotifyPlaylistTracksPaging,
    SpotifyTrackDetails,
)

from app.domain.exceptions.spotify_exception import SpotifyAuthorizeError,SpotifyAPIError
from app.application.services.http_service import HttpService

class SpotifyPublicService:
    """
    Сервис для взаимодействия с публичным Spotify API (без авторизации пользователя),
    используя Client Credentials Flow.
    """
    SPOTIFY_API_BASE_URL = 'https://api.spotify.com/v1'
    SPOTIFY_AUTH_URL = 'https://accounts.spotify.com/api/token'
    
    def __init__(self,http_service: HttpService):
        self.http_service = http_service
    
    _access_token = None
    _token_expires_at = 0


    async def _get_access_token_client(self) -> str:
        """
        Получает клиентский токен для доступа к публичному API Spotify.
        Если токен уже есть и не истёк, возвращает его.
        """
        if self._token_expires_at > time.time():
            return self._access_token

        token_url = f"{self.SPOTIFY_AUTH_URL}"
        token_data = {
            'grant_type': 'client_credentials',
            'client_id': settings.spotify.SPOTIFY_CLIENT_ID,
            'client_secret': settings.spotify.SPOTIFY_CLIENT_SECRET,
        }
        try:
            spotify_token = self.http_service.handle_request(url=token_url,data=token_data,method='post')

            self._access_token = spotify_token.get('access_token')
            self._token_expires_at = int(time.time() + spotify_token.get('expires_in'))

            return self._access_token
        except httpx.HTTPStatusError as e:
            raise SpotifyAuthorizeError(
                status_code=e.response.status_code,
                detail=f"Ошибка авторизации Spotify (Client Credentials Flow): {e.response.text}"
            )
        
    async def _make_spotify_request(self,method: str,endpoint: str, **kwargs) -> dict[str,str]:
        """
        Вспомогательный метод для выполнения запросов к Spotify API.
        """
        headers = {
            "Authorization": f"Bearer {self._access_token}"
        }

        full_url = self.SPOTIFY_API_BASE_URL + endpoint

        try:
            return await self.http_service.make_request(method, full_url,headers=headers, **kwargs)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise SpotifyAuthorizeError(detail="Требуется переавторизация")
        
            raise SpotifyAPIError(
                status_code=e.response.status_code,
                detail=f"Ошибка Spotify ({endpoint}): {e.response.text}"
            )
        
        
    async def search_public_track(self,query: str, limit: int = 10) -> dict[str,str]:
        """
        Ищет треки на Spotify (публичный поиск).
        """
        await self._get_access_token_client()
        return await self._make_spotify_request(
            'GET',
            '/search',
            params={'q':query,'type':'track','limit':str(limit)}
        )
    
    async def search_track_by_spotify_id(self,spotify_id: str) -> dict[str, str]:
        """
        Получает детальную информацию о треке по его Spotify ID (публичный доступ).
        """
        await self._get_access_token_client()
        return await self._make_spotify_request(
            'GET',
            '/tracks',
            params={'q':spotify_id,'type':'track'}
        )
    
    async def search_public_playlists(self,query: str, limit: int = 10) -> list[SpotifyPlaylistsSearchPaging]:
        """
        Ищет плейлисты на Spotify по названию (публичный поиск).
        Возвращает объект SpotifyPlaylistsSearchPaging, содержащий пагинацию и список плейлистов.
        """
        response_data = await self._make_spotify_request(
            'GET',
            '/search',
            params={'q':query,'type':'playlist','limit': limit}
        )
        if 'playlists' in response_data:
            return SpotifyPlaylistsSearchPaging.model_validate(response_data['playlists'])
    

    
    async def get_public_playlist_tracks(self, playlist_id: str) -> list[SpotifyTrackDetails]:
        """
        Получает все воспроизводимые треки из указанного плейлиста Spotify (публичный доступ).
        Обрабатывает пагинацию и возвращает список объектов SpotifyTrackDetails.
        """
        all_tracks: list[SpotifyTrackDetails] = []
        offset = 0
        limit = 50 

        while True:
            response_data = await self._make_spotify_request(
                'GET',
                f'/playlists/{playlist_id}/tracks',
                params={'limit': limit, 'offset': offset}
            )
            
            tracks_page = SpotifyPlaylistTracksPaging.model_validate(response_data)
            
            for item in tracks_page.items:
                if item.track and item.track.is_playable: 
                    all_tracks.append(item.track)
            
           
            if tracks_page.next:
                offset += limit
            else:
                break 

        return all_tracks
        
        