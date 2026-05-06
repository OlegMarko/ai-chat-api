import json
import redis
from typing import List, Dict
from app.core import settings

client = redis.Redis.from_url(settings.redis_url, decode_responses=True)


def _key(session_id: str) -> str:
    return f"chat:{session_id}"


def get_history(session_id: str) -> List[Dict[str, str]]:
    raw = client.lrange(_key(session_id), 0, -1)

    return [json.loads(item) for item in raw]


def add_message(session_id: str, role: str, content: str):
    key = _key(session_id)
    if len(content) > 5000:
        content = content[:5000]

    message = json.dumps({"role": role, "content": content})

    client.rpush(key, message)
    client.ltrim(key, -settings.history_max_len, -1)
    client.expire(key, settings.history_ttl)


def clear_history(session_id: str):
    client.delete(_key(session_id))
