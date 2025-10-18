from redis.asyncio import Redis, ConnectionPool
from src.api.core.configs import settings
import logging

logger = logging.getLogger(__name__)

_redis_pool: ConnectionPool | None = None
_redis_client: Redis | None = None


async def get_redis() -> Redis:
    """Get Redis client instance."""
    global _redis_pool, _redis_client

    if _redis_client is None:
        _redis_pool = ConnectionPool.from_url(
            settings.redis_url,
            decode_responses=True,
            max_connections=10
        )
        _redis_client = Redis(connection_pool=_redis_pool)
        logger.info(f"Redis connected: {settings.redis_url}")

    return _redis_client


async def close_redis():
    """Close Redis connection."""
    global _redis_pool, _redis_client

    if _redis_client:
        await _redis_client.aclose()
        _redis_client = None
        logger.info("Redis connection closed")

    if _redis_pool:
        await _redis_pool.disconnect()
        _redis_pool = None
