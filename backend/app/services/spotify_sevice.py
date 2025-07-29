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

        # Возвращаем актуальный токен доступа
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