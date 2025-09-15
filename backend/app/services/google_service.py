from app.models import User
from sqlalchemy.orm import Session
from app.config.settings import settings
import httpx
from fastapi import HTTPException,status
import time
from app.services.user_service import UserService
from app.logger.log_config import logger

class GoogleService:

    GOOGLE_API_BASE_URl = 'https://oauth2.googleapis.com'

    def __init__(self,db: Session,user: User):
        self.db = db
        self.user = user


    
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
            logger.error('GoogleService: У пользователя %s отсутствует Google Refresh Token',str(self.user.id),)
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
                logger.debug('GoogleService: Делаем запрос в Google для обновления токена по URl %s',token_url)
                response = await client.post(url=token_url, data=token_data)
                response.raise_for_status()
                new_tokens: dict = response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == status.HTTP_400_BAD_REQUEST:
                logger.error('GoogleService: Произошла ошибка во время обновления токена пользователя %s',str(self.user.id))
                UserService.update_user_profile(self.db, self.user, {
                    'google_access_token': None,
                    'google_refresh_token': None,
                    'google_token_expires_at': None
                })
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Токен обновления Google недействителен. Пожалуйста, переавторизуйтесь в Google."
                )
            logger.error('GoogleService: Произошла ошибка во время обновления токена пользователя %s.%r',str(self.user.id),e.response.text,exc_info=True)
            raise HTTPException(
                status_code=e.response.status_code,
                detail="Ошибка при обновлении токена Google"
            )
        except Exception:
            logger.error('GoogleService: Неизвестная ошибка при обновлении токена Google: %r',exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Неизвестная ошибка при обновлении токена Google"
            )
        logger.debug('GoogleService: Запрос прошел успешно')
        
        update_data = {
            'google_access_token': new_tokens.get('access_token'),
            'google_token_expires_at': int(time.time()) + new_tokens['expires_in']
        }
        
        if 'refresh_token' in new_tokens:
            update_data['google_refresh_token'] = new_tokens['refresh_token']
        logger.debug('GoogleService: Токен успешно обновлен')


        UserService.update_user_profile(self.db, self.user, update_data)
        
        return new_tokens