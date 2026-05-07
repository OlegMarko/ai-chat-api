import asyncio
import random
from collections.abc import Awaitable, Callable
from typing import TypeVar

from openai import APIConnectionError, APIStatusError, APITimeoutError, RateLimitError

from app.core.config import settings

T = TypeVar("T")


def _retryable_openai(exc: BaseException) -> bool:
    if isinstance(exc, (APITimeoutError, RateLimitError, APIConnectionError)):
        return True

    status = getattr(exc, "status_code", None)

    return isinstance(exc, APIStatusError) and status is not None and status >= 500


async def with_openai_backoff(coro_provider: Callable[[], Awaitable[T]]) -> T:
    attempts = settings.openai_max_retries + 1
    delay = settings.openai_retry_min_wait_seconds
    max_delay = settings.openai_retry_max_wait_seconds

    exc_last: BaseException | None = None

    for attempt_ix in range(1, attempts + 1):
        try:
            return await coro_provider()
        except BaseException as err:
            exc_last = err

            if attempt_ix >= attempts or not _retryable_openai(err):
                raise err

            jitter = delay * random.uniform(0.8, 1.2)

            backoff_slice = jitter + float(attempt_ix**2) * 0.05

            resting_interval = float(min(backoff_slice, max_delay))

            await asyncio.sleep(resting_interval)
            delay = float(min(delay * 2.0, max_delay))

    assert exc_last is not None
    raise exc_last


async def retry_openai(
    _operation_slug: str, coro_provider: Callable[[], Awaitable[T]]
) -> T:
    return await with_openai_backoff(coro_provider)
