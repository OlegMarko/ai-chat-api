from sqlalchemy import text

from app.db.database import engine
from app.db.models import Base


# python scripts/init_db.py
def init_db():
    Base.metadata.create_all(bind=engine)

    with engine.connect() as conn:
        conn.execute(
            text(
                """
                CREATE INDEX IF NOT EXISTS
                document_chunks_embedding_hnsw

                ON document_chunks

                USING hnsw (
                    embedding vector_cosine_ops
                )

                WITH (
                    m = 16,
                    ef_construction = 64
                );
                """
            )
        )

        conn.commit()

    print("- Database initialized")
    print("- HNSW index created")


if __name__ == "__main__":
    init_db()
