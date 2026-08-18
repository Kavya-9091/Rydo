from redis.asyncio import Redis

from app.core.settings import get_settings


async def get_redis_client() -> Redis:
    settings = get_settings()
    return Redis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)
