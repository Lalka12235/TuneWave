from time import time
from typing import Any

import httpx
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.logger.log_config import logger
from app.models.user import User
from app.schemas.spotify_schemas import (
    SpotifyPlaylistsSearchPaging,
    SpotifyPlaylistTracksPaging,
    SpotifyTrackDetails,
)
from app.services.spotify_public_service import SpotifyPublicService


class SpotifyService:
    """
    Сервис для взаимодействия со Spotify API, используя как пользовательскую авторизацию,
    так и публичные возможности через SpotifyPublicService.
    """

    SPOTIFY_API_BASE_URL = "https://api.spotify.com/v1"
    SPOTIFY_ACCOUNTS_BASE_URL = "https://accounts.spotify.com/api"

    def __init__(self,db: Session,user: User,spotify_public: SpotifyPublicService | None = None):
        self.db = db
        self.user = user
        self._check_user_spotify_credentials()
        self.spotify_public_service = spotify_public

    
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
                logger.info(f'SpotifyService: Отправляем запрос на Spotify API для получения устройств пользователя {self.user.id} по адресу: {device_url}')
                response = await client.get(url=device_url, headers=headers)
                response.raise_for_status()
                
                devices_data: dict = response.json()
                devices_list = devices_data.get('devices', [])


                if not devices_list:
                    logger.info(f'SpotifyService: Для пользователя {self.user.id} не обнаружено активных устройств Spotify.')
                    return None

                for device in devices_list:
                    if device.get('is_active'):
                        logger.info(f"SpotifyService: Найдено активное устройство '{device.get('name')}' (ID: {device.get('id')}) для пользователя {self.user.id}.")
                        return device.get('id')
                logger.info(f"SpotifyService: У пользователя {self.user.id} нет активных устройств.")
                return None
        except httpx.HTTPStatusError as e:
            logger.warning(f"SpotifyService: Ошибка HTTP при получении устройств Spotify для пользователя {self.user.id}: Статус {e.response.status_code} - Ответ: {e.response.text}", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"SpotifyService: Непредвиденная ошибка при получении устройств Spotify для пользователя {self.user.id}: {e}", exc_info=True)
            return None

        return None



    def _check_user_spotify_credentials(self):
        """
        Проверяет наличие необходимых токенов Spotify у пользователя.
        """
        if not self.user.spotify_access_token or not self.user.spotify_refresh_token:
            logger.error(f'SpotifyService: Отсутствуют токены Spotify у пользователя {self.user.id}.')
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
            logger.info(f'SpotifyService: Токен Spotify пользователя {self.user.id} истек или отсутствует, инициируем обновление.')
            await self._refresh_access_token()
        else:
            logger.debug(f"SpotifyService: Используем действующий токен Spotify для пользователя {self.user.id}. Истекает через {self.user.spotify_token_expires_at - current_time} сек.")

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
                logger.info(f"SpotifyService: Отправляем запрос на обновление токена Spotify для пользователя {self.user.id} по адресу: {token_url}")
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
                logger.error(f"SpotifyService: Ошибка 400 при обновлении токена Spotify для пользователя {self.user.id}. Refresh-токен недействителен. Ответ: {e.response.text}", exc_info=True)
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Токен обновления Spotify недействителен. Пожалуйста, переавторизуйтесь в Spotify."
                )
            logger.error(f"SpotifyService: Ошибка HTTP при обновлении токена Spotify для пользователя {self.user.id}: Статус {e.response.status_code} - Ответ: {e.response.text}", exc_info=True)
            raise HTTPException(
                status_code=e.response.status_code,
                detail="Ошибка при обновлении токена Spotify"
            )
        except Exception as e:
            logger.error(f"SpotifyService: Неизвестная ошибка при обновлении токена Spotify для пользователя {self.user.id}: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Неизвестная ошибка при обновлении токена Spotify"
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
                logger.debug(f"SpotifyService: Выполняем запрос '{method} {endpoint}' для пользователя {self.user.id}.")
                response = await client.request(method, full_url, headers=headers, **kwargs)
                response.raise_for_status()
                spotify_response = response.json()
                return spotify_response
        except httpx.HTTPStatusError as e:
            logger.error(f"SpotifyService: Ошибка HTTP при запросе '{method} {endpoint}' для пользователя {self.user.id}: Статус {e.response.status_code} - Ответ: {e.response.text}", exc_info=True)
            if e.response.status_code == status.HTTP_401_UNAUTHORIZED:
                logger.warning(f"SpotifyService: Получен 401 Unauthorized для пользователя {self.user.id} на эндпоинте {endpoint}. Пытаемся обновить токен и повторить запрос.")
                try:
                    await self._refresh_access_token()
                    headers = await self._get_auth_headers() 
                    async with httpx.AsyncClient() as client:
                        response = await client.request(method, full_url, headers=headers, **kwargs)
                        response.raise_for_status()
                        spotify_response = response.json()
                        logger.info(f"SpotifyService: Запрос '{method} {endpoint}' успешно выполнен после обновления токена для пользователя {self.user.id}.")
                        return spotify_response
                except HTTPException as refresh_exc:
                    logger.error(f"SpotifyService: Не удалось повторить запрос после обновления токена для пользователя {self.user.id}: {refresh_exc.detail}", exc_info=True)
                    raise refresh_exc
                except Exception as retry_exc:
                    logger.error(f"SpotifyService: Неизвестная ошибка при повторной попытке запроса к Spotify API после обновления токена для пользователя {self.user.id}: {retry_exc}", exc_info=True)
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Не удалось выполнить запрос к Spotify API после обновления токена."
                    )
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Ошибка Spotify API ({endpoint}): {e.response.text}"
            )
        except Exception as e:
            logger.error(f"SpotifyService: Неизвестная ошибка при запросе к Spotify API ({endpoint}) для пользователя {self.user.id}: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Неизвестная ошибка при запросе к Spotify API ({endpoint}): {e}"
            )
        
        
    async def search_track(self,query: str, limit: int = 10) -> list[SpotifyTrackDetails]:
        """
        Ищет треки на Spotify.
        """
        response_data = await self._make_spotify_request(
            'GET',
            '/search',
            params={'q': query, 'type': 'track', 'limit': limit}
        )
        if 'tracks' in response_data and 'items' in response_data['tracks']:
            tracks_list = [
                SpotifyTrackDetails.model_validate(item) # item - это уже объект трека
                for item in response_data['tracks']['items'] 
                if item # Убеждаемся, что элемент не None
            ]
            logger.info(f"SpotifyService: Найдены треки для запроса '{query}'. Количество: {len(tracks_list)}.")
            return tracks_list
        logger.warning(f"SpotifyService: Поиск треков Spotify для запроса '{query}' не вернул ожидаемую структуру 'tracks.items': {response_data}")
        return [] # Возвращаем пустой список, если структура ответа не та.
    


    async def play(self, device_id: str, track_uri: str | None = None, uris: list[str] | None = None, position_ms: int = 0):
        """
        Запускает воспроизведение трека или списка треков на указанном устройстве.
        """
        play_url_endpoint = '/me/player/play'
        body = {}
        
        # Если передан список URI (для воспроизведения плейлиста или нескольких треков)
        if uris:
            body['uris'] = uris
            logger.info(f"SpotifyService: Запрос на запуск воспроизведения списка URI на устройстве '{device_id}' для пользователя {self.user.id}.")
        # Если передан один URI трека
        elif track_uri:
            body['uris'] = [track_uri]
            logger.info(f"SpotifyService: Запрос на запуск воспроизведения трека '{track_uri}' на устройстве '{device_id}' для пользователя {self.user.id}.")
        # Если ни URI, ни список URI не указаны, просто возобновляем воспроизведение
        else:
            logger.info(f"SpotifyService: Запрос на возобновление воспроизведения на устройстве '{device_id}' для пользователя {self.user.id}.")
        
        # Устанавливаем позицию воспроизведения, если она больше 0
        if position_ms > 0:
            body['position_ms'] = position_ms

        try:
            # Отправляем запрос
            await self._make_spotify_request(
                'PUT',
                play_url_endpoint,
                params={'device_id': device_id},
                json=body # Используем json=body для httpx для отправки JSON-тела
            )
            logger.info(f"SpotifyService: Команда 'play' успешно отправлена для пользователя {self.user.id} на устройство '{device_id}'.")
        except Exception as e:
            logger.error(f"SpotifyService: Ошибка при отправке команды 'play' для пользователя {self.user.id}: {e}", exc_info=True)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Не удалось отправить команду воспроизведения Spotify.")


    async def pause(self, device_id: str):
        """
        Ставит воспроизведение на паузу на указанном устройстве.
        """
        try:
            logger.info(f"SpotifyService: Отправляем команду 'pause' на устройство '{device_id}' для пользователя {self.user.id}.")
            await self._make_spotify_request(
                'PUT',
                '/me/player/pause',
                params={'device_id': device_id}
            )
            logger.info(f"SpotifyService: Команда 'pause' успешно отправлена для пользователя {self.user.id}.")
        except Exception as e:
            logger.error(f"SpotifyService: Ошибка при отправке команды 'pause' для пользователя {self.user.id}: {e}", exc_info=True)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Не удалось отправить команду паузы Spotify.")


    async def skip_next(self, device_id: str):
        """
        Переключает на следующий трек на указанном устройстве.
        """
        try:
            logger.info(f"SpotifyService: Отправляем команду 'skip next' на устройство '{device_id}' для пользователя {self.user.id}.")
            await self._make_spotify_request(
                'POST', # Для next/previous используется POST, не PUT
                '/me/player/next',
                params={'device_id': device_id}
            )
            logger.info(f"SpotifyService: Команда 'skip next' успешно отправлена для пользователя {self.user.id}.")
        except Exception as e:
            logger.error(f"SpotifyService: Ошибка при отправке команды 'skip next' для пользователя {self.user.id}: {e}", exc_info=True)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Не удалось отправить команду 'следующий трек' Spotify.")

    async def skip_previous(self, device_id: str):
        """
        Переключает на предыдущий трек на указанном устройстве.
        """
        try:
            logger.info(f"SpotifyService: Отправляем команду 'skip previous' на устройство '{device_id}' для пользователя {self.user.id}.")
            await self._make_spotify_request(
                'POST', # Для next/previous используется POST, не PUT
                '/me/player/previous',
                params={'device_id': device_id}
            )
            logger.info(f"SpotifyService: Команда 'skip previous' успешно отправлена для пользователя {self.user.id}.")
        except Exception as e:
            logger.error(f"SpotifyService: Ошибка при отправке команды 'skip previous' для пользователя {self.user.id}: {e}", exc_info=True)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Не удалось отправить команду 'предыдущий трек' Spotify.")


    async def get_playback_state(self) -> dict[str, Any] | None:
        """
        Получает текущее состояние плеера Spotify для авторизованного пользователя.
        """
        state_url_endpoint = '/me/player'
        
        try:
            state_response = await self._make_spotify_request('GET', state_url_endpoint)
            
            if not state_response: 
                logger.info(f"SpotifyService: Нет активного плеера для пользователя {self.user.id} (ответ 204 No Content от Spotify).")
                return None

            progress_ms = state_response.get('progress_ms')
            is_playing = state_response.get('is_playing')
            duration_ms = state_response.get('item', {}).get('duration_ms')
            
            current_track_data = state_response.get('item')
            current_track_details: SpotifyTrackDetails | None = None
            if current_track_data:
                try:
                    current_track_details = SpotifyTrackDetails.model_validate(current_track_data)
                except Exception as e:
                    logger.warning(f"SpotifyService: Не удалось валидировать текущий трек Spotify из-за ошибки схемы: {e}", exc_info=True)

            logger.info(f"SpotifyService: Получено состояние плеера для пользователя {self.user.id}. Is playing: {is_playing}, Progress: {progress_ms}ms.")
            return {
                "progress_ms": progress_ms,
                "is_playing": is_playing,
                "duration_ms": duration_ms,
                "current_track": current_track_details 
            }
        except HTTPException as e:
            if e.status_code == status.HTTP_204_NO_CONTENT: 
                logger.info(f"SpotifyService: Для пользователя {self.user.id} нет активного плеера Spotify (204 No Content).")
                return None
            logger.error(f"SpotifyService: Ошибка HTTP при получении состояния плеера для пользователя {self.user.id}: {e.detail}", exc_info=True)
            raise e 
        except Exception as e:
            logger.error(f"SpotifyService: Непредвиденная ошибка при получении состояния плеера Spotify для пользователя {self.user.id}: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Не удалось получить состояние плеера Spotify из-за внутренней ошибки сервера."
            )
        
    
    async def smart_search_tracks(self, query: str, limit: int = 10) -> dict:
        """
        Умный поиск треков.
        Сначала пытается использовать токен пользователя.
        Если токена нет, использует публичный поиск.
        """
        if self.user.spotify_access_token and self.user.spotify_token_expires_at > time.time():
            return await self.search_track(query, limit)
        else:
            return await self.spotify_public_service.search_public_track(query, limit)
        
    
    async def search_track_by_spotify_id(self,spotify_id: str) -> dict[str, Any]:
        """
        Ищет треки на Spotify по Spotify ID
        """
        return await self._make_spotify_request(
            'GET',
            '/tracks',
            params={'q':spotify_id,'type':'track'}
        )
    
    async def search_playlists(self,query: str, limit: int = 10) -> list[SpotifyPlaylistsSearchPaging]:
        """
        Ищет плейлисты на Spotify по названию
        Возвращает объект SpotifyPlaylistsSearchPaging, содержащий пагинацию и список плейлистов.
        """
        response_data = await self._make_spotify_request(
            'GET',
            '/search',
            params={'q':query,'type':'playlist','limit': limit}
        )
        if 'playlists' in response_data:
            return SpotifyPlaylistsSearchPaging.model_validate(response_data['playlists'])
    

    async def get_playlist_tracks(self, playlist_id: str) -> list[SpotifyTrackDetails]:
        """
        Получает все воспроизводимые треки из указанного плейлиста Spotify.
        Обрабатывает пагинацию и возвращает список объектов SpotifyTrackDetails.
        """
        all_tracks: list[SpotifyTrackDetails] = []
        offset = 0
        limit = 50 

        while True:
            logger.debug(f"SpotifyService: Получаем треки для плейлиста '{playlist_id}' с offset={offset}, limit={limit}.")
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

        logger.info(f"SpotifyService: Получено {len(all_tracks)} воспроизводимых треков из плейлиста '{playlist_id}' для пользователя {self.user.id}.")
        return all_tracks