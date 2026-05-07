from sqlalchemy.ext.asyncio import AsyncSession

from openai import AsyncOpenAI

from app.core.config import settings
from app.repositories.vector_repository import VectorRepository
from app.services.embeddings import embed_query

_VECTOR_REPOSITORY = VectorRepository()


async def retrieve(
    session: AsyncSession,
    *,
    embedding_client: AsyncOpenAI,
    question: str,
    limit: int | None = None,
) -> list[dict]:
    resolved_limit = limit if limit is not None else settings.retrieval_ann_limit

    query_vector = await embed_query(embedding_client, question)

    rows = await _VECTOR_REPOSITORY.similarity_search(
        session,
        embedding=query_vector,
        limit=resolved_limit,
    )

    print("*" * 10)
    print(rows)
    print("*" * 10)

    out: list[dict] = []
    for row in rows:
        out.append(
            {
                "text": row.content,
                "metadata": {"source": row.source, "chunk_id": row.chunk_id},
                "distance": getattr(row, "distance", None),
            },
        )

    return out
