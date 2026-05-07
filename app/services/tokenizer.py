import tiktoken

from app.core.config import settings

_encoding_cache: dict[str, tiktoken.Encoding] = {}


def _encoding_for_chat_budget() -> tiktoken.Encoding:
    model = settings.tiktoken_budget_model_override or settings.chat_model_name
    cached = _encoding_cache.get(model)
    if cached is not None:
        return cached

    try:
        enc = tiktoken.encoding_for_model(model)
        _encoding_cache[model] = enc
        return enc
    except KeyError:
        enc = tiktoken.get_encoding("o200k_base")
        _encoding_cache[settings.chat_model_name] = enc
        return enc


def count_tokens(text: str) -> int:
    return len(_encoding_for_chat_budget().encode(text))


def truncate_to_token_budget(text: str, max_tokens: int) -> str:
    enc = _encoding_for_chat_budget()
    tokens = enc.encode(text)
    if len(tokens) <= max_tokens:
        return text
    return enc.decode(tokens[:max_tokens])
