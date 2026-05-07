from app.services.tokenizer import count_tokens


def build_token_aware_history(messages, max_tokens=1000):
    """
    messages: list[{"role": str, "content": str}]
    """

    selected = []
    total_tokens = 0

    for msg in reversed(messages):
        tokens = count_tokens(msg["content"])

        if total_tokens + tokens > max_tokens:
            break

        selected.append(msg)
        total_tokens += tokens

    return list(reversed(selected))
