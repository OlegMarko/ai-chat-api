from app.repositories.vector_repository import VectorRepository
from app.services.embeddings import embed_texts

repo = VectorRepository()


def retrieve(question: str, limit=10):
    query_embedding = embed_texts([question])[0]

    rows = repo.similarity_search(
        embedding=query_embedding,
        limit=limit,
    )

    docs = []

    for row in rows:
        docs.append(
            {
                "text": row.content,
                "metadata": {
                    "source": row.source,
                    "chunk_id": row.chunk_id,
                },
            }
        )

    return docs
