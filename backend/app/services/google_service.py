import time

import httpx
from app.config.settings import settings
from app.models import User
from app.services.user_service import UserService

from app.exceptions.exception import ServerError
from app.exceptions.user_exception import UserNotAuthorized



class GoogleService:

    GOOGLE_API_BASE_URl = 'https://oauth2.googleapis.com'

    def __init__(self,user: User,user_service: UserService):
        self.user = user
        self.user_service = user_service


    
    async def _refresh_access_token(self) -> dict:
        """
        Делает запрос к Google API для обновления access_token с помощью refresh_token.
        Обновляет токены в базе данных.
        
        Returns:
            dict: Словарь с новым access_token и другой информацией.
        
        Raises:
            HTTPException: Если refresh_token отсутствует или недействителен.
        """
        if not self.user.google_refresh_token:
            raise UserNotAuthorized(
                detail="Отсутствует refresh token Google. Требуется повторная авторизация."
            )
            
        token_url = f"{self.GOOGLE_API_BASE_URl}/token"
        token_data = {
            'grant_type': 'refresh_token',
            'refresh_token': self.user.google_refresh_token,
            'client_id': settings.google.GOOGLE_CLIENT_ID,
            'client_secret': settings.google.GOOGLE_CLIENT_SECRET,
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url=token_url, data=token_data)
                response.raise_for_status()
                new_tokens: dict = response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 400:
                UserService.update_user_profile(self.user, {
                    'google_access_token': None,
                    'google_refresh_token': None,
                    'google_token_expires_at': None
                })
                raise ServerError(
                    detail="Токен обновления Google недействителен. Пожалуйста, переавторизуйтесь в Google."
                )
            raise ServerError(
                detail=f"Ошибка при обновлении токена Google: {e.response.text}"
            )
        except Exception as e:
            raise ServerError(
                detail=f"Неизвестная ошибка при обновлении токена Google: {e}"
            )
        
        update_data = {
            'google_access_token': new_tokens.get('access_token'),
            'google_token_expires_at': int(time.time()) + new_tokens['expires_in']
        }
        
        if 'refresh_token' in new_tokens:
            update_data['google_refresh_token'] = new_tokens['refresh_token']
        
        self.user_service.update_user_profile(self.user, update_data)
        
        return new_tokens