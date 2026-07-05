import redis.asyncio as aioredis
from core.config import settings

redis_client: aioredis.Redis | None = None


async def init_redis():
    global redis_client
    redis_client = aioredis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        password=settings.REDIS_PASSWORD or None,
        db=settings.REDIS_DB,
        decode_responses=True,
    )
    await redis_client.ping()


async def close_redis():
    global redis_client
    if redis_client:
        await redis_client.close()


async def get_redis() -> aioredis.Redis:
    return redis_client
