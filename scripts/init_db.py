"""Sync DDL bootstrap (tables + HNSW). Run: `python scripts/init_db.py`"""

from sqlalchemy import create_engine, text

from app.core.config import settings
from app.db.database import Base, sync_database_url_for_scripts
from app.db.models import DocumentChunk


DDL_VECTOR = """
CREATE EXTENSION IF NOT EXISTS vector
"""

DDL_HNSW = """
CREATE INDEX IF NOT EXISTS document_chunks_embedding_hnsw
ON document_chunks USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64)
"""


def init_db() -> None:
    sync_url = sync_database_url_for_scripts(settings.database_url)

    engine = create_engine(sync_url)

    with engine.connect() as conn:
        conn.execute(text(DDL_VECTOR))
        conn.commit()

    Base.metadata.create_all(bind=engine)

    with engine.connect() as conn:
        conn.execute(text(DDL_HNSW))
        conn.commit()


if __name__ == "__main__":
    init_db()

    print("Schema + HNSW index ready.")
