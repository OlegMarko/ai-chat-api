from typing import Annotated

from fastapi import Depends, Request
from openai import AsyncOpenAI
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_async_session

SessionDepAnnotated = Annotated[AsyncSession, Depends(get_async_session)]


async def redis_tcp(request: Request) -> Redis:
    return Redis(connection_pool=request.app.state.redis_pool)


async def openai_shared(request: Request) -> AsyncOpenAI:
    return request.app.state.shared_openai


RedisDepAnnotated = Annotated[Redis, Depends(redis_tcp)]
OpenAIDepAnnotated = Annotated[AsyncOpenAI, Depends(openai_shared)]
