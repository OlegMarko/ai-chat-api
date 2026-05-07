import logging

from sqlalchemy import Row, select, delete, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models import DocumentChunk

logger = logging.getLogger(__name__)


class VectorRepository:
    async def similarity_search(
        self,
        session: AsyncSession,
        *,
        embedding: list[float],
        limit: int = 64,
        ef_search_hint: int | None = None,
    ):
        ef_value = int(
            ef_search_hint
            if ef_search_hint is not None
            else settings.hnsw_ef_search
        )

        await session.execute(
            text(f"SET LOCAL hnsw.ef_search = {ef_value}")
        )

        stmt = (
            select(
                DocumentChunk.id,
                DocumentChunk.source,
                DocumentChunk.chunk_id,
                DocumentChunk.content,
                DocumentChunk.embedding.cosine_distance(embedding).label(
                    "distance"
                ),
            )
            .order_by(
                DocumentChunk.embedding.cosine_distance(embedding)
            )
            .limit(limit)
        )

        result = await session.execute(stmt)

        return list(result.fetchall())

    async def delete_source(self, session: AsyncSession, source: str) -> None:
        await session.execute(
            delete(DocumentChunk).where(DocumentChunk.source == source)
        )
