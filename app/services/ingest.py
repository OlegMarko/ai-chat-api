from sqlalchemy.ext.asyncio import AsyncSession

from openai import AsyncOpenAI

from app.core.config import settings
from app.db.models import DocumentChunk
from app.repositories.vector_repository import VectorRepository
from app.services.chunker import chunk_words
from app.services.embeddings import embed_texts

VECTOR_REPO = VectorRepository()


async def ingest_document_async(
    session: AsyncSession,
    embedding_client: AsyncOpenAI,
    *,
    source: str,
    text: str,
) -> int:
    await VECTOR_REPO.delete_source(session, source)

    chunks = chunk_words(text, chunk_words=300, overlap_words=50)

    if not chunks:
        return 0

    embeddings = await embed_texts(embedding_client, chunks)

    if (
        settings.embedding_dimensions
        and len(embeddings[0]) != settings.embedding_dimensions
    ):
        raise ValueError(
            f"embedding dim mismatch ({len(embeddings[0])} != {settings.embedding_dimensions})"
        )

    rows: list[DocumentChunk] = []
    for i, chunk in enumerate(chunks):
        rows.append(
            DocumentChunk(
                source=source,
                chunk_id=i,
                content=chunk,
                embedding=list(embeddings[i]),
            ),
        )

    session.add_all(rows)

    return len(rows)
