from time import time
import httpx
from app.exceptions.exception import ServerError
from app.logger.log_config import logger

async def _generic_refresh_token(
    self,
    token_url: str,
    key_prefix: str,
    refresh_token: str,
    client_id: str,
    client_secret: str,
    api_name: str,
) -> dict:
    """Универсальная логика обновления токена OAuth."""
    
    key_config = f'{key_prefix}:{self.user.id}:config'
    key_access = f'{key_prefix}:{self.user.id}:access'
    
    token_data = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
        'client_id': client_id,
        'client_secret': client_secret
    }
    
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}

    try:
        async with httpx.AsyncClient() as client:
            logger.info(f"{api_name}Service: Отправляем запрос на обновление токена для пользователя {self.user.id}")
            response = await client.post(url=token_url, data=token_data, headers=headers)
            response.raise_for_status()
            new_tokens: dict = response.json()
            
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 400:
            hset_dict = {
                'refresh_token': None,
                'expires_at': 0
            }
            await self.redis_service.hset(key_config, hset_dict)
            await self.redis_service.set(key_access,None,0)
            logger.error(f"{api_name}Service: Ошибка 400. Refresh-токен недействителен.", exc_info=True)
            raise ServerError(
                detail=f"Токен обновления {api_name} недействителен. Пожалуйста, переавторизуйтесь."
            )
        
        logger.error(f"{api_name}Service: Ошибка HTTP при обновлении токена: {e.response.text}", exc_info=True)
        raise ServerError(
            detail=f"Ошибка при обновлении токена {api_name}"
        )
    except Exception as e:
        logger.error(f"{api_name}Service: Неизвестная ошибка при обновлении токена: {e}", exc_info=True)
        raise ServerError(
            detail=f"Неизвестная ошибка при обновлении токена {api_name}"
        )

    access_token = new_tokens.get('access_token')
    new_refresh_token = new_tokens.get('refresh_token', refresh_token)
    token_expires_at = int(time() + new_tokens['expires_in'])

    hset_dict = {
        'refresh_token': new_refresh_token,
        'expires_at': token_expires_at
    }
    await self.redis_service.set(key_access, access_token, token_expires_at)
    await self.redis_service.hset(key_config, hset_dict)
    return new_tokens