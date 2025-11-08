from time import time
from typing import Any

import httpx

from app.config.settings import settings
from app.logger.log_config import logger
from app.schemas.entity import UserEntity
from app.schemas.spotify_schemas import (
    SpotifyPlaylistsSearchPaging,
    SpotifyPlaylistTracksPaging,
    SpotifyTrackDetails,
)

from app.exceptions.exception import ServerError
from app.exceptions.spotify_exception import SpotifyAPIError,SpotifyAuthorizeError,CommandError
from app.services.redis_service import RedisService
from app.services.base_oauth_service import _generic_refresh_token


class SpotifyService:
    """
    Сервис для взаимодействия со Spotify API, используя как пользовательскую авторизацию.
    """

    SPOTIFY_API_BASE_URL = "https://api.spotify.com/v1"
    SPOTIFY_ACCOUNTS_BASE_URL = "https://accounts.spotify.com/api"

    def __init__(self,user: UserEntity,redis_service: RedisService):
        self.user = user
        self.redis_service = redis_service
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
        key = f'spotify_auth:{self.user.id}'
        access_token,refresh_token,_ = self.redis_service.get(key)
        if not access_token and not refresh_token:
            logger.error(f'SpotifyService: Отсутствуют токены Spotify у пользователя {self.user.id}.')
            raise SpotifyAuthorizeError(
                detail="Пользователь не авторизован в Spotify или токены отсутствуют."
            )

    async def _get_auth_headers(self) -> dict[str, str]:
        """
        Получает заголовки авторизации с актуальным токеном доступа Spotify.
        Обновляет токен, если он истек.
        """
        current_time = int(time()) 
        key = f'spotify_auth:{self.user.id}'
        access_token,refresh_token,expires_at = self.redis_service.get(key)
        if expires_at is None or \
           expires_at <= (current_time + 300):
            logger.info(f'SpotifyService: Токен Spotify пользователя {self.user.id} истек или отсутствует, инициируем обновление.')
            await self._refresh_access_token()
        else:
            logger.debug(f"SpotifyService: Используем действующий токен Spotify для пользователя {self.user.id}. Истекает через {expires_at - current_time} сек.")

        return {
            "Authorization": f"Bearer {access_token}"
        }
    
    async def _refresh_access_token(self) -> dict[str, str]:
        """
        Обновляет токен доступа Spotify с использованием токена обновления.
        """
        token_url = f"{self.SPOTIFY_ACCOUNTS_BASE_URL}/token"
        key = f'spotify_auth:{self.user.id}'
        
        tokens_str = await self.redis_service.get(key)
        if not tokens_str or tokens_str == f'{None}:{None}:{None}':
            raise SpotifyAuthorizeError(detail="Отсутствует refresh token Spotify.")
            
        _, refresh_token, _ = tokens_str.split(':')
        
        new_tokens = await _generic_refresh_token(
            self=self,
            token_url=token_url,
            key_prefix='spotify_auth',
            refresh_token=refresh_token,
            client_id=settings.spotify.SPOTIFY_CLIENT_ID,
            client_secret=settings.spotify.SPOTIFY_CLIENT_SECRET,
            api_name='Spotify',
        )
    
        return {'status': 'success', 'detail': 'refresh token'}

    async def _make_spotify_request(self,method: str,endpoint: str, **kwargs) -> dict[str,str]:
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
            if e.response.status_code == 401:
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
                except Exception as retry_exc:
                    logger.error(f"SpotifyService: Неизвестная ошибка при повторной попытке запроса к Spotify API после обновления токена для пользователя {self.user.id}: {retry_exc}", exc_info=True)
                    raise ServerError(
                        detail="Не удалось выполнить запрос к Spotify API после обновления токена."
                    )
            raise SpotifyAPIError(
                status_code=e.response.status_code,
                detail=f"Ошибка Spotify API ({endpoint}): {e.response.text}"
            )
        except Exception as e:
            logger.error(f"SpotifyService: Неизвестная ошибка при запросе к Spotify API ({endpoint}) для пользователя {self.user.id}: {e}", exc_info=True)
            raise SpotifyAPIError(
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
                if item
            ]
            logger.info(f"SpotifyService: Найдены треки для запроса '{query}'. Количество: {len(tracks_list)}.")
            return tracks_list
        logger.warning(f"SpotifyService: Поиск треков Spotify для запроса '{query}' не вернул ожидаемую структуру 'tracks.items': {response_data}")
        return []
    


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
        
        if position_ms > 0:
            body['position_ms'] = position_ms

        try:
            await self._make_spotify_request(
                'PUT',
                play_url_endpoint,
                params={'device_id': device_id},
                json=body
            )
            logger.info(f"SpotifyService: Команда 'play' успешно отправлена для пользователя {self.user.id} на устройство '{device_id}'.")
        except Exception as e:
            logger.error(f"SpotifyService: Ошибка при отправке команды 'play' для пользователя {self.user.id}: {e}", exc_info=True)
            raise CommandError(detail="Не удалось отправить команду воспроизведения Spotify.")


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
            raise CommandError(etail="Не удалось отправить команду паузы Spotify.")


    async def skip_next(self, device_id: str):
        """
        Переключает на следующий трек на указанном устройстве.
        """
        try:
            logger.info(f"SpotifyService: Отправляем команду 'skip next' на устройство '{device_id}' для пользователя {self.user.id}.")
            await self._make_spotify_request(
                'POST',
                '/me/player/next',
                params={'device_id': device_id}
            )
            logger.info(f"SpotifyService: Команда 'skip next' успешно отправлена для пользователя {self.user.id}.")
        except Exception as e:
            logger.error(f"SpotifyService: Ошибка при отправке команды 'skip next' для пользователя {self.user.id}: {e}", exc_info=True)
            raise CommandError(detail="Не удалось отправить команду 'следующий трек' Spotify.")

    async def skip_previous(self, device_id: str):
        """
        Переключает на предыдущий трек на указанном устройстве.
        """
        try:
            logger.info(f"SpotifyService: Отправляем команду 'skip previous' на устройство '{device_id}' для пользователя {self.user.id}.")
            await self._make_spotify_request(
                'POST',
                '/me/player/previous',
                params={'device_id': device_id}
            )
            logger.info(f"SpotifyService: Команда 'skip previous' успешно отправлена для пользователя {self.user.id}.")
        except Exception as e:
            logger.error(f"SpotifyService: Ошибка при отправке команды 'skip previous' для пользователя {self.user.id}: {e}", exc_info=True)
            raise CommandError(detail="Не удалось отправить команду 'предыдущий трек' Spotify.")


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
        except SpotifyAPIError as e:
            raise e 
        except Exception as e:
            logger.error(f"SpotifyService: Непредвиденная ошибка при получении состояния плеера Spotify для пользователя {self.user.id}: {e}", exc_info=True)
            raise ServerError(
                detail="Не удалось получить состояние плеера Spotify из-за внутренней ошибки сервера."
            )
        
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