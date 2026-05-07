"""Redis-backed rate limit gate (AsyncMock, no server)."""

from __future__ import annotations

import asyncio

import pytest
from fastapi import HTTPException
from unittest.mock import AsyncMock

from app.security.ratelimit import enforce_rate_limit_minute_bucket


def test_enforce_rate_limit_skips_when_max_zero() -> None:
    redis = AsyncMock()

    async def run() -> None:
        await enforce_rate_limit_minute_bucket(
            redis,
            bucket_name="t",
            client_subject="peer",
            max_calls=0,
        )

    asyncio.run(run())

    redis.incr.assert_not_called()


def test_enforce_rate_limit_blocks_when_over_cap() -> None:
    redis = AsyncMock()
    redis.incr = AsyncMock(return_value=11)
    redis.expire = AsyncMock(return_value=True)

    async def run() -> None:
        with pytest.raises(HTTPException) as ctx:
            await enforce_rate_limit_minute_bucket(
                redis,
                bucket_name="chat",
                client_subject="127.0.0.1",
                max_calls=10,
            )
        assert ctx.value.status_code == 429
        assert ctx.value.detail == "rate_limit_exceeded"

    asyncio.run(run())
    redis.expire.assert_not_called()


def test_enforce_rate_limit_sets_ttl_on_first_window_key() -> None:
    redis = AsyncMock()
    redis.incr = AsyncMock(return_value=1)
    redis.expire = AsyncMock(return_value=True)

    async def run() -> None:
        await enforce_rate_limit_minute_bucket(
            redis,
            bucket_name="chat",
            client_subject="client-a",
            max_calls=100,
        )

    asyncio.run(run())

    redis.expire.assert_awaited_once()
