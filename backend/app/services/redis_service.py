from redis.asyncio import Redis
from app.logger.log_config import logger
import json
from typing import Callable,Any

class RedisService:

    def __init__(self,client: Redis):
        self._client = client

    
    async def get(self,key: str) -> dict[str,str]:
        try:
            cached_item = await self._client.get(key)
            if cached_item:
                logger.info('RedisService: Возвращаю данные полученные по ключу %s',key)
                return json.loads(cached_item)
        except Exception as e:
            logger.error('RedisService: ошибка при получение кэша %r',e,exc_info=True)

    async def set(self,key: str,value: str,expiration: int) -> bool:
        """
        Сохраняет значение в кэш. Значение сериализуется в JSON (default=str для дат/UUID).
        expiration — TTL в секундах.
        """
        try:
            payload = json.dumps(value, default=str, ensure_ascii=False)
            await self._client.set(key, payload, ex=expiration)
            logger.debug("RedisService: set key=%s ttl=%s", key, expiration)
            return True
        except Exception as e:
            logger.error("RedisService: set error for key=%s: %s", key, e, exc_info=True)
            return False 


    async def get_or_set(self,key: str,fetch_func: Callable,expiration: int,*args,**kwargs) -> Any:
        cached_data = self.get(key)
        if cached_data:
            return cached_data
        try:
            result = await fetch_func(*args,**kwargs)
            await self.set(key,result,expiration)
            return result
        except Exception as e:
            logger.exception("RedisService: fetch_func failed for key=%s: %s", key, e,exc_info=True)
            raise

    
    async def hget(self,key: str) -> dict[str,str] | None:
        try:
            result = await self._client.hgetall(key)
            if not result:
                logger.info('RedisService: Данные не найдены')
                return None
            result = {
                k.decode('utf-8'): v.decode('utf-8')
                for k,v in result.items()
            }
            logger.info('RedisService: Возвращаю данные по ключу %s',key)
            return result
        except Exception as e:
            logger.error('RedisService: ошибка при получение кэша %r',e,exc_info=True)

    
    async def hset(self,key: str,data: dict[str,str]) -> bool:
        try:
            await self._client.hset(key,mapping=data)
            return True
        except Exception as e:
            logger.error("RedisService: set error for key=%s: %s", key, e, exc_info=True)
            return False
