import redis

from redis.asyncio import Redis
from redis.asyncio.connection import ConnectionPool

from app.config.settings import settings
from app.config.log_config import logger


redis_pool = ConnectionPool(
    max_connections=10
)

async_redis_client: Redis = Redis(
    connection_pool=redis_pool,
    host=settings.redis.REDIS_HOST,
    port=settings.redis.REDIS_PORT,
    db=0,
    decode_responses=True
)

async def get_redis_client():
    logger.info("Attempting to get Redis client...")
    try:
        await async_redis_client.ping()
        logger.info("Successfully connected to Redis.")
        return async_redis_client
    except redis.exceptions.ConnectionError as e:
        logger.error(f"Could not connect to Redis: {e}", exc_info=True)
        return None