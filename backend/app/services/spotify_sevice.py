from fastapi import HTTPException,status
from sqlalchemy.orm import Session
from app.models.user import User
from time import time
from typing import Any
import httpx
from app.config.settings import settings


class SpotifyService:

    SPOTIFY_API_BASE_URL = "https://api.spotify.com/v1"
    SPOTIFY_ACCOUNTS_BASE_URL = "https://accounts.spotify.com/api"

    def __init__(self,db: Session,user: User):
        self.db = db
        self.user = user
        self._check_user_spotify_credentials()

    
    async def _get_device_id(self, access_token: str) -> str | None:
        """
        Получает ID активного устройства пользователя Spotify.

        Args:
            access_token (str): Токен доступа Spotify.

        Returns:
            str | None: ID активного устройства или None, если оно не найдено.
        """
        device_url = f'{self.SPOTIFY_API_BASE_URL}/me/player/devices'
        headers = {
            'Authorization': f'Bearer {access_token}'
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url=device_url, headers=headers)
                response.raise_for_status()
                
                devices_data: dict = response.json()
                devices_list = devices_data.get('devices', [])

                if not devices_list:
                    return None

                for device in devices_list:
                    if device.get('is_active'):
                        return device.get('id')

        except httpx.HTTPStatusError as e:
            print(f"Ошибка HTTP: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            print(f"Произошла непредвиденная ошибка: {e}")
            return None

        return None



    def _check_user_spotify_credentials(self):
        """
        Проверяет наличие необходимых токенов Spotify у пользователя.
        """
        if not self.user.spotify_access_token or not self.user.spotify_refresh_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пользователь не авторизован в Spotify или токены отсутствуют."
            )

    async def _get_auth_headers(self) -> dict[str, str]:
        """
        Получает заголовки авторизации с актуальным токеном доступа Spotify.
        Обновляет токен, если он истек.
        """
        current_time = int(time()) 
        if self.user.spotify_token_expires_at is None or \
           self.user.spotify_token_expires_at <= (current_time + 300):
            await self._refresh_access_token()

        return {
            "Authorization": f"Bearer {self.user.spotify_access_token}"
        }
    
    async def _refresh_access_token(self) -> dict[str,str]:
        """
        Обновляет токен доступа Spotify с использованием токена обновления.
        Сохраняет новый токен и время его истечения в базу данных.
        """
        token_url = f"{self.SPOTIFY_ACCOUNTS_BASE_URL}/token"

        token_data = {
            'grant_type': 'refresh_token',
            'refresh_token': self.user.spotify_refresh_token,
            'client_id': settings.SPOTIFY_CLIENT_ID,
            'client_secret': settings.SPOTIFY_CLIENT_SECRET
        }

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url=token_url, data=token_data, headers=headers)
                response.raise_for_status()
                new_tokens: dict = response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == status.HTTP_400_BAD_REQUEST:
                self.user.spotify_access_token = None
                self.user.spotify_refresh_token = None
                self.user.spotify_token_expires_at = None
                self.db.add(self.user)
                self.db.commit()
                # userRepository.update_user(self.db,self.user.id,{'spotify_access_token':None...})
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Токен обновления Spotify недействителен. Пожалуйста, переавторизуйтесь в Spotify."
                )
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Ошибка при обновлении токена Spotify: {e.response.text}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Неизвестная ошибка при обновлении токена Spotify: {e}"
            )
        
        self.user.spotify_access_token = new_tokens.get('access_token')
        self.user.spotify_refresh_token = new_tokens.get('refresh_token',self.user.spotify_refresh_token)
        self.user.spotify_token_expires_at = int(time()+ new_tokens['expires_in'])
        
        self.db.add(self.user)
        self.db.commit()
        self.db.refresh(self.user)
        
        return {
            'status': 'success',
            'detail': 'refresh token'
        }
    

    async def _make_spotify_request(self,method: str,endpoint: str, **kwargs) -> dict[str,Any]:
        """
        Вспомогательный метод для выполнения запросов к Spotify API.
        """
        headers = await self._get_auth_headers()

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
        
        
    async def search_track(self,query: str, limit: int = 10) -> dict[str,Any]:
        """
        Ищет треки на Spotify.
        """
        return await self._make_spotify_request('GET','/search',params={'q':query,'type':'track','limit':str(limit)})
    


    async def play(self, access_token: str, device_id: str, track_uri: str = None):
        """Запускает воспроизведение трека на указанном устройстве."""
        # Отправить запрос на Spotify API: PUT /me/player/play
        # В теле запроса можно указать URI трека, чтобы начать играть с него.
        pass


    async def pause(self, access_token: str, device_id: str):
        """Ставит воспроизведение на паузу."""
        # Отправить запрос на Spotify API: PUT /me/player/pause
        pass


    async def skip(self, access_token: str, device_id: str):
        """Переключает на следующий трек."""
        # Отправить запрос на Spotify API: POST /me/player/next
        pass


    async def get_playback_state(self) -> dict[str, Any] | None:
        """
        Получает текущее состояние плеера Spotify для авторизованного пользователя.

        Returns:
            dict[str, Any] | None: Словарь с состоянием плеера или None в случае ошибки.
        """
        state_url = f'{self.SPOTIFY_API_BASE_URL}/me/player'
        headers = {
            'Authorization': f'Bearer {self.current_user.spotify_access_token}'
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url=state_url, headers=headers)
                response.raise_for_status()

                state_response: dict = response.json()
                
                progress_ms = state_response.get('progress_ms')
                is_playing = state_response.get('is_playing')
                duration_ms = state_response.get('item', {}).get('duration_ms')

                return {
                    "progress_ms": progress_ms,
                    "is_playing": is_playing,
                    "duration_ms": duration_ms
                }
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 204:
                return None
            else:
                print(f"Ошибка HTTP: {e.response.status_code} - {e.response.text}")
                return None
        except Exception as e:
            print(f"Произошла непредвиденная ошибка: {e}")
            return None