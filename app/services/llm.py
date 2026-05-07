import logging
from collections.abc import AsyncIterator

from openai import AsyncOpenAI
from redis.asyncio import Redis

from app.core.config import settings
from app.core.exceptions import LLMServiceError
from app.services.history import add_message, get_history
from app.services.history_builder import build_token_aware_history
from app.services.retry_policies import retry_openai

logger = logging.getLogger(__name__)


def _estimate_cost_prompt_completion(
    *, prompt_tokens: int, completion_tokens: int
) -> float:
    pt = prompt_tokens / 1000 * settings.price_per_1k_prompt_tokens_usd
    ct = completion_tokens / 1000 * settings.price_per_1k_completion_tokens_usd
    return pt + ct


async def generate_response(
    *,
    redis: Redis,
    client: AsyncOpenAI,
    session_id: str,
    message: str,
    rag_mode: bool = False,
) -> str:
    max_completion_tokens = (
        settings.rag_max_completion_tokens
        if rag_mode
        else settings.chat_max_completion_tokens
    )
    model_to_use = (
        settings.effective_rag_chat_model() if rag_mode else settings.chat_model_name
    )

    history_raw = await get_history(redis, session_id)

    trimmed_history = build_token_aware_history(
        history_raw,
        max_prompt_tokens_budget=settings.chat_history_prompt_token_budget,
    )

    chat_messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        *trimmed_history,
        {"role": "user", "content": message},
    ]

    await add_message(redis, session_id, "user", message)

    logger.info(
        "llm_request_start session_id=%s rag_mode=%s model=%s",
        session_id,
        rag_mode,
        model_to_use,
    )

    async def _call_completion() -> str:
        response = await client.chat.completions.create(
            model=model_to_use,
            messages=chat_messages,
            max_tokens=max_completion_tokens,
            timeout=settings.openai_chat_timeout_seconds,
            temperature=0.2 if rag_mode else 0.7,
        )

        if not response.choices or response.choices[0].message is None:
            raise LLMServiceError("Empty response from LLM")

        maybe = response.choices[0].message.content
        if not maybe:
            raise LLMServiceError("Empty response from LLM")

        usage_obj = getattr(response, "usage", None)
        if usage_obj is not None:
            pt = getattr(usage_obj, "prompt_tokens", None) or 0
            ct_u = getattr(usage_obj, "completion_tokens", None) or 0
            estimate = _estimate_cost_prompt_completion(
                prompt_tokens=pt, completion_tokens=ct_u
            )
            logger.info(
                "llm_usage_prompt_completion prompt_tokens=%s completion_tokens=%s est_cost_usd=%.6f",
                pt,
                ct_u,
                estimate,
            )

        return maybe

    try:
        content = await retry_openai("chat_completion_non_stream", _call_completion)
        await add_message(redis, session_id, "assistant", content)

        logger.info(
            "llm_request_completed session_id=%s rag_mode=%s",
            session_id,
            rag_mode,
        )

        return content

    except LLMServiceError:
        raise

    except Exception as exc:
        logger.warning(
            "chat_completion_failure session_id=%s error=%s",
            session_id,
            type(exc).__name__,
        )
        raise LLMServiceError("Failed to generate assistant response.") from exc


async def generate_response_stream(
    *,
    redis: Redis,
    client: AsyncOpenAI,
    session_id: str,
    message: str,
    rag_mode: bool = False,
) -> AsyncIterator[str]:
    max_completion_tokens = (
        settings.rag_max_completion_tokens
        if rag_mode
        else settings.chat_max_completion_tokens
    )
    model_to_use = (
        settings.effective_rag_chat_model() if rag_mode else settings.chat_model_name
    )

    history_raw = await get_history(redis, session_id)

    trimmed_history = build_token_aware_history(
        history_raw,
        max_prompt_tokens_budget=settings.chat_history_prompt_token_budget,
    )

    chat_messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        *trimmed_history,
        {"role": "user", "content": message},
    ]

    await add_message(redis, session_id, "user", message)

    async def mk_stream():
        return await client.chat.completions.create(
            model=model_to_use,
            messages=chat_messages,
            max_tokens=max_completion_tokens,
            timeout=settings.openai_chat_timeout_seconds,
            temperature=0.2 if rag_mode else 0.7,
            stream=True,
        )

    try:
        stream = await retry_openai(
            "chat_completion_stream_outer",
            mk_stream,
        )

        combined: list[str] = []

        async for chunk in stream:
            choice = chunk.choices[0].delta.content if chunk.choices else None
            if choice:
                combined.append(choice)
                yield choice

        final_text = "".join(combined)

        if final_text:
            await add_message(redis, session_id, "assistant", final_text)

    except LLMServiceError:
        raise

    except Exception as exc:
        logger.warning(
            "chat_stream_failure session_id=%s error=%s",
            session_id,
            type(exc).__name__,
        )
        raise LLMServiceError("Streaming response failed.") from exc
