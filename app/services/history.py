import json
from typing import Any

from redis.asyncio import Redis

from app.core.config import settings


def _key(session_id: str) -> str:
    return f"chat:v1:{session_id}"


async def get_history(redis: Redis, session_id: str) -> list[dict[str, Any]]:
    raw = await redis.lrange(_key(session_id), 0, -1)
    parsed: list[dict[str, Any]] = []
    for item in raw:
        parsed.append(json.loads(item))
    return parsed


async def add_message(
    redis: Redis,
    session_id: str,
    role: str,
    content: str,
) -> None:
    cap = settings.history_message_byte_cap
    if len(content.encode("utf-8")) > cap:
        content_bytes = content.encode("utf-8")[:cap]
        content = content_bytes.decode("utf-8", errors="ignore")

    message = json.dumps({"role": role, "content": content})

    await redis.rpush(_key(session_id), message)

    maxlen = settings.history_max_messages
    await redis.ltrim(_key(session_id), -maxlen, -1)

    await redis.expire(_key(session_id), settings.history_ttl_seconds)


async def clear_history(redis: Redis, session_id: str) -> None:
    await redis.delete(_key(session_id))
