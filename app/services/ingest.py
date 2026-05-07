from app.db.models import DocumentChunk
from app.repositories.vector_repository import VectorRepository

from app.services.chunker import chunk_text
from app.services.embeddings import embed_texts


repo = VectorRepository()


def ingest_document(text: str, source: str):
    chunks = chunk_text(text)

    embeddings = embed_texts(chunks)

    rows = []

    for i, chunk in enumerate(chunks):
        rows.append(
            DocumentChunk(
                source=source,
                chunk_id=i,
                content=chunk,
                embedding=embeddings[i],
            )
        )

    repo.insert_chunks(rows)
