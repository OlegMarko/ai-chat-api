"""OpenAI retry helper: retryable vs fatal errors."""

from __future__ import annotations

import asyncio

import httpx
import pytest
from openai import RateLimitError

from app.core.config import settings
from app.services.retry_policies import retry_openai


async def _raises(exc: BaseException) -> str:
    raise exc


def test_retry_openai_non_retryable_propagates_immediately() -> None:
    async def bad() -> str:
        await _raises(RuntimeError("fatal"))

    with pytest.raises(RuntimeError, match="fatal"):
        asyncio.run(retry_openai("op", bad))


def test_retry_openai_rate_limit_then_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "openai_max_retries", 2)
    monkeypatch.setattr(settings, "openai_retry_min_wait_seconds", 0.0)
    monkeypatch.setattr(settings, "openai_retry_max_wait_seconds", 0.01)

    req = httpx.Request("POST", "https://api.openai.com/v1/chat/completions")
    res = httpx.Response(429, request=req)

    calls = {"n": 0}

    async def flaky() -> str:
        calls["n"] += 1
        if calls["n"] == 1:
            raise RateLimitError(message="rate limited", response=res, body={})
        return "ok"

    assert asyncio.run(retry_openai("op", flaky)) == "ok"
    assert calls["n"] == 2
