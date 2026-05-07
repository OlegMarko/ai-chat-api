from openai import AsyncOpenAI

from app.core.config import settings


def create_shared_llm_client() -> AsyncOpenAI:
    timeout_seconds = max(
        settings.openai_chat_timeout_seconds,
        settings.openai_embedding_timeout_seconds,
    )

    return AsyncOpenAI(
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
        timeout=timeout_seconds,
        max_retries=0,
    )
