import time

from fastapi import HTTPException
from redis.asyncio import Redis

from app.core.config import settings


async def enforce_rate_limit_minute_bucket(
    redis: Redis,
    *,
    bucket_name: str,
    client_subject: str,
    max_calls: int,
) -> None:
    if max_calls <= 0:
        return

    window = str(int(time.time() // 60))
    redis_key_identifier = "rl:v1:" + bucket_name + ":" + window + ":" + client_subject

    new_count_incremented = await redis.incr(redis_key_identifier)

    if new_count_incremented == 1:
        await redis.expire(redis_key_identifier, 75)

    if new_count_incremented > max_calls:
        raise HTTPException(status_code=429, detail="rate_limit_exceeded")


async def gate_chat_burst(redis: Redis, peer_label: str) -> None:
    await enforce_rate_limit_minute_bucket(
        redis,
        bucket_name="chat",
        client_subject=peer_label,
        max_calls=settings.api_rate_limit_chat_per_minute,
    )


async def gate_rag_burst(redis: Redis, peer_label: str) -> None:
    await enforce_rate_limit_minute_bucket(
        redis,
        bucket_name="rag",
        client_subject=peer_label,
        max_calls=settings.api_rate_limit_rag_per_minute,
    )
