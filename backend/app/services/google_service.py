import time

import httpx
from fastapi import HTTPException, status, Depends
from typing import Annotated

from app.config.settings import settings
from app.models.user import User
from app.services.dep import get_user_service
from app.services.user_service import UserService



class GoogleService:

    GOOGLE_API_BASE_URl = 'https://oauth2.googleapis.com'

    def __init__(self,user: User,user_service: Annotated[UserService,Depends(get_user_service)]):
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
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Отсутствует refresh token Google. Требуется повторная авторизация."
            )
            
        token_url = f"{self.GOOGLE_API_BASE_URl}/token"
        token_data = {
            'grant_type': 'refresh_token',
            'refresh_token': self.user.google_refresh_token,
            'client_id': settings.GOOGLE_CLIENT_ID,
            'client_secret': settings.GOOGLE_CLIENT_SECRET,
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url=token_url, data=token_data)
                response.raise_for_status()
                new_tokens: dict = response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == status.HTTP_400_BAD_REQUEST:
                UserService.update_user_profile(self.db, self.user, {
                    'google_access_token': None,
                    'google_refresh_token': None,
                    'google_token_expires_at': None
                })
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Токен обновления Google недействителен. Пожалуйста, переавторизуйтесь в Google."
                )
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Ошибка при обновлении токена Google: {e.response.text}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
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