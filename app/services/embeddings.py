from openai import AsyncOpenAI

from app.core.config import settings
from app.services.retry_policies import retry_openai


async def _embed_single_batch(
    client: AsyncOpenAI, texts: list[str]
) -> list[list[float]]:
    response = await client.embeddings.create(
        model=settings.embedding_model_name,
        input=texts,
        dimensions=settings.embedding_dimensions,
        timeout=settings.openai_embedding_timeout_seconds,
    )

    vectors = sorted(response.data, key=lambda entry: getattr(entry, "index", 0))

    return [list(entry.embedding) for entry in vectors]


async def embed_texts(client: AsyncOpenAI, texts: list[str]) -> list[list[float]]:
    results: list[list[float]] = []
    batch_size = 96

    for batch_start_pointer in range(0, len(texts), batch_size):
        sliced_batch_candidate = texts[
            batch_start_pointer : batch_start_pointer + batch_size
        ]

        embeddings_slice = await retry_openai(
            f"embeddings_slice_{batch_start_pointer}",
            lambda sb=list(sliced_batch_candidate): _embed_single_batch(client, sb),
        )

        results.extend(embeddings_slice)

    return results


async def embed_query(client: AsyncOpenAI, text_value: str) -> list[float]:
    vectors_bundle = await embed_texts(client, [text_value])
    return vectors_bundle[0]
