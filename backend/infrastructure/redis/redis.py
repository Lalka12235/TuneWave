import redis

from redis.asyncio import Redis
from redis.asyncio.connection import ConnectionPool

from app.config.settings import settings
from app.logger.log_config import logger


redis_pool = ConnectionPool(
    host=settings.redis.REDIS_HOST,
    port=settings.redis.REDIS_PORT,
    db=0, 
    decode_responses=True 
)

async_redis_client: Redis = Redis(connection_pool=redis_pool)

async def get_redis_client():
    """
    Создает асинхронный клиент Redis.
    Эта функция будет использоваться как зависимость FastAPI (Depends).
    """
    logger.info("Attempting to get Redis client...")
    try:
        await async_redis_client.ping()
        logger.info("Successfully connected to Redis.")
        return async_redis_client
    except redis.exceptions.ConnectionError as e:
        logger.error(f"Could not connect to Redis: {e}", exc_info=True)
        return None