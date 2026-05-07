from sqlalchemy import text

from app.db.database import SessionLocal
from app.db.models import DocumentChunk


class VectorRepository:
    def __init__(self):
        self.db = SessionLocal()

    def insert_chunks(self, rows):
        self.db.bulk_save_objects(rows)
        self.db.commit()

    def similarity_search(self, embedding, limit=5):
        sql = text(
            """
            SELECT
                id,
                source,
                chunk_id,
                content,
                embedding <=> :embedding AS distance
            FROM document_chunks
            ORDER BY embedding <=> :embedding
            LIMIT :limit
            """
        )

        result = self.db.execute(
            sql,
            {
                "embedding": embedding,
                "limit": limit,
            },
        )

        return result.fetchall()
