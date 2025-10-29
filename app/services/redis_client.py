from typing import Optional
from redis.asyncio import Redis, ConnectionPool
from app.core.config import settings


_pool: Optional[ConnectionPool] = None


def _get_pool() -> ConnectionPool:
    global _pool
    if _pool is None:
        _pool = ConnectionPool.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            health_check_interval=30,
            max_connections=20,
        )
    return _pool


async def get_redis() -> Redis:
    return Redis(connection_pool=_get_pool())


async def close_redis() -> None:
    global _redis
    if _redis is not None:
        await _redis.close()
        _redis = None
