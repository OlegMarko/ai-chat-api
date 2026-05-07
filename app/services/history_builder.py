from app.core.config import settings
from app.services.tokenizer import count_tokens


def build_token_aware_history(
    messages: list[dict[str, str]],
    *,
    max_prompt_tokens_budget: int,
) -> list[dict[str, str]]:
    margin = settings.chat_history_system_margin_tokens + 48
    budget = max(0, max_prompt_tokens_budget - margin)

    selected: list[dict[str, str]] = []
    total_tokens = 0

    for msg in reversed(messages):
        content = msg.get("content", "")
        tokens = count_tokens(content)
        if total_tokens + tokens > budget:
            break

        selected.append(msg)
        total_tokens += tokens

    return list(reversed(selected))
