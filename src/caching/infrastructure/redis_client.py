from functools import lru_cache

from redis.asyncio import Redis

from src.core.config import get_settings


@lru_cache
def get_redis_client() -> Redis:
    settings = get_settings()
    return Redis.from_url(settings.redis_url, decode_responses=True)


async def ping_redis() -> bool:
    settings = get_settings()
    if not settings.redis_enabled:
        return True

    try:
        redis = get_redis_client()
        return bool(await redis.ping())
    except Exception:
        return False


async def close_redis_client() -> None:
    if get_redis_client.cache_info().currsize == 0:
        return

    redis = get_redis_client()
    await redis.aclose()
    get_redis_client.cache_clear()
