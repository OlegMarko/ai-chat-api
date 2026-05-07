import logging
import time
from openai import OpenAI
from app.core import settings, LLMServiceError
from app.services.history import get_history, add_message
from app.services.history_builder import build_token_aware_history

logger = logging.getLogger(__name__)

client = OpenAI(api_key=settings.openai_api_key)


def calculate_cost(total_tokens: int) -> float:
    return (total_tokens / 1000) * settings.price_per_1k_tokens


def generate_response(message: str, session_id: str) -> str:
    logger.info(f"Generating response | message_length={len(message)}")
    history = get_history(session_id)
    history = build_token_aware_history(history, max_tokens=1000)

    messages = [
        {"role": "system", "content": "You are a helpful assistant"},
        *history,
        {"role": "user", "content": message},
    ]

    add_message(session_id, "user", message)

    for attempt in range(settings.retries):
        try:
            start_time = time.time()

            response = client.chat.completions.create(
                model=settings.model_name,
                messages=messages,
                max_tokens=settings.max_tokens,
                timeout=settings.timeout,
            )

            latency = time.time() - start_time

            if not response.choices or not response.choices[0].message.content:
                raise LLMServiceError("Empty response from LLM")

            content = response.choices[0].message.content

            usage = getattr(response, "usage", None)
            if usage:
                total_tokens = usage.total_tokens
                cost = calculate_cost(total_tokens)

                logger.info(f"LLM usage | tokens={total_tokens} | cost=${cost:.6f}")

            add_message(session_id, "assistant", content)
            logger.info(f"LLM latency={latency:.2f}s")

            return content

        except Exception as e:
            logger.warning(f"LLM attempt {attempt + 1} failed")

            if attempt == settings.retries - 1:
                logger.exception("LLM call failed after retries")
                raise LLMServiceError("Failed after retries") from e

            time.sleep(settings.delay * (2**attempt))
