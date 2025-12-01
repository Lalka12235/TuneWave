from app.config.settings import settings
from app.domain.entity import UserEntity

from app.domain.exceptions.user_exception import UserNotAuthorized
from app.application.services.redis_service import RedisService
from app.application.services.base_oauth_service import _generic_refresh_token



class GoogleService:

    GOOGLE_API_BASE_URl = 'https://oauth2.googleapis.com'

    def __init__(self,user: UserEntity,redis_service: RedisService):
        self.user = user
        self.redis_service = redis_service

    async def _refresh_access_token(self) -> dict:
        """
        Делает запрос к Google API для обновления access_token с помощью refresh_token.
        """
        token_url = f"{self.GOOGLE_API_BASE_URl}/token"
        key = f'google_auth:{self.user.id}:config'
        
        tokens_str:dict = await self.redis_service.hget(key)
        if not tokens_str:
            raise UserNotAuthorized(detail="Отсутствует refresh token Google.")
            
        refresh_token = tokens_str.get('refresh_token')
        
        new_tokens = await _generic_refresh_token(
            self=self,
            token_url=token_url,
            key_prefix='google_auth',
            refresh_token=refresh_token,
            client_id=settings.google.GOOGLE_CLIENT_ID,
            client_secret=settings.google.GOOGLE_CLIENT_SECRET,
            api_name='Google',
        )
        
        return new_tokens