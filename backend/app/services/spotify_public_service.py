from app.config.settings import settings
import httpx
from fastapi import HTTPException, status
import time
from typing import Any


class SpotifyPublicService:

    SPOTIFY_API_BASE_URL = 'https://api.spotify.com/v1'
    SPOTIFY_AUTH_URL = 'https://accounts.spotify.com/api/token'
    
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
            'client_id': settings.SPOTIFY_CLIENT_ID,
            'client_secret': settings.SPOTIFY_CLIENT_SECRET,
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url=token_url,data=token_data)
                response.raise_for_status()
                spotify_token: dict = response.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Ошибка авторизации Spotify (Client Credentials Flow): {e.response.text}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Неизвестная ошибка при получении токена Spotify: {e}"
            )


        self._access_token = spotify_token.get('access_token')
        self._token_expires_at = int(time.time() + spotify_token.get('expires_in'))

        return self._token_expires_at
    
        
    async def _make_spotify_request(self,method: str,endpoint: str, **kwargs) -> dict[str,Any]:
        """
        Вспомогательный метод для выполнения запросов к Spotify API.
        """
        headers = {
            "Authorization": f"Bearer {self._access_token}"
        }

        full_url = self.SPOTIFY_API_BASE_URL + endpoint

        try:
            async with httpx.AsyncClient() as client:
                response = await client.request(method, full_url, headers=headers, **kwargs)
                response.raise_for_status()
                spotify_response = response.json()
                return spotify_response
        except httpx.HTTPStatusError as e:
            if e.response.status_code == status.HTTP_401_UNAUTHORIZED:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Неавторизованный запрос к Spotify API. Возможно, требуется переавторизация: {e.response.text}"
                )
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Ошибка Spotify API ({endpoint}): {e.response.text}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Неизвестная ошибка при запросе к Spotify API ({endpoint}): {e}"
            )
        
        
    async def search_public_track(self,query: str, limit: int = 10) -> dict[str,Any]:
        """
        Ищет треки на Spotify.
        """
        await self._get_access_token_client()
        return await self._make_spotify_request(
            'GET',
            '/search',
            params={'q':query,'type':'track','limit':str(limit)}
        )
