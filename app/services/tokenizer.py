import tiktoken
from app.core.config import settings

_encoding = tiktoken.encoding_for_model(settings.model_name)


def count_tokens(text: str) -> int:
    return len(_encoding.encode(text))
