import asyncio
import redis.asyncio as redis_asyncio
from app.core.config import settings


def create_connection_pool() -> redis_asyncio.ConnectionPool:
    return redis_asyncio.ConnectionPool.from_url(
        settings.redis_url,
        max_connections=settings.redis_pool_max_connections,
        decode_responses=True,
        encoding="utf-8",
    )


async def disconnect_pool(pool: redis_asyncio.ConnectionPool) -> None:
    disconnect = getattr(pool, "disconnect", None)

    if disconnect is None:
        return

    maybe_future = disconnect()

    if asyncio.iscoroutine(maybe_future):
        await maybe_future
