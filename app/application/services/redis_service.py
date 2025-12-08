from redis.asyncio import Redis
from app.config.log_config import logger
import json
from typing import Callable,Any

class RedisService:

    def __init__(self,client: Redis):
        self._client = client

    
    async def get(self,key: str) -> Any | None:
        try:
            cached_item = await self._client.get(key)
            if cached_item:
                logger.info('RedisService: Возвращаю данные полученные по ключу %s',key)
                return json.loads(cached_item)
        except Exception as e:
            logger.error('RedisService: ошибка при получение кэша %r',e,exc_info=True)

    async def set(self,key: str,value: Any,expiration: int | None = None) -> bool:
        try:
            payload = json.dumps(value, default=str, ensure_ascii=False)
            await self._client.set(key, payload, ex=expiration)
            logger.debug("RedisService: set key=%s ttl=%s", key, expiration)
            return True
        except Exception as e:
            logger.error("RedisService: set error for key=%s: %s", key, e, exc_info=True)
            return False 

    async def default_delete(self,key: str) -> bool:
        try:
            await self._client.delete(key)
            return True
        except Exception as e:
            return False


    async def get_or_set(self,key: str,fetch_func: Callable,expiration: int,*args,**kwargs) -> Any:
        cached_data = self.get(key)
        if cached_data:
            return cached_data
        try:
            #todo пересмотреть этот вызов
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

    async def lpush(self, name: str, value: str) -> bool:
        """Добавляет элемент в начало списка."""
        try:
            await self._client.lpush(name, value)
            return True
        except Exception as e:
            # Добавлено логирование
            logger.error("RedisService: lpush error for name=%s: %s", name, e, exc_info=True)
            return False

    async def rpush(self, name: str, value: Any) -> bool:
        """Добавляет элемент в конец списка."""
        try:
            await self._client.rpush(name, value)
            return True
        except Exception as e:
            # Добавлено логирование
            logger.error("RedisService: rpush error for name=%s: %s", name, e, exc_info=True)
            return False

    async def lrange(self, name: str, start: int = 0, end: int = -1) -> list[str]:
        """Возвращает диапазон элементов списка."""
        try:
            # Добавлен await
            return await self._client.lrange(name=name, start=start, end=end)
        except Exception as e:
            # Добавлено логирование
            logger.error("RedisService: lrange error for name=%s: %s", name, e, exc_info=True)
            return []

    async def rpop(self, name: str) -> str:
        """Удаляет и возвращает последний элемент списка."""
        try:
            # Добавлен await
            result = await self._client.rpop(name=name)
            if result:
                # Декодирование, если возвращаются байты
                return result.decode('utf-8') if isinstance(result, bytes) else result
            return ''
        except Exception as e:
            # Добавлено логирование
            logger.error("RedisService: rpop error for name=%s: %s", name, e, exc_info=True)
            return ''

    async def lpop(self, name: str) -> str:
        """Удаляет и возвращает первый элемент списка."""
        try:
            # Добавлен await
            result = await self._client.lpop(name=name)
            if result:
                # Декодирование, если возвращаются байты
                return result.decode('utf-8') if isinstance(result, bytes) else result
            return ''
        except Exception as e:
            # Добавлено логирование
            logger.error("RedisService: lpop error for name=%s: %s", name, e, exc_info=True)
            return ''

    async def length_list(self, name: str) -> int:
        """Возвращает длину списка."""
        try:
            # Добавлен await
            length = await self._client.llen(name=name)
            return length if length is not None else 0
        except Exception as e:
            # Добавлено логирование
            logger.error("RedisService: length_list error for name=%s: %s", name, e, exc_info=True)
            return 0

    async def lrem(self, key: str, value: Any, count: int = 1) -> bool:
        """Удаляет элементы из списка."""
        try:
            await self._client.lrem(key, count, value)
            return True
        except Exception as e:
            # Добавлено логирование
            logger.error("RedisService: lrem error for key=%s: %s", key, e, exc_info=True)
            return False