from collections import defaultdict

from app.services.embeddings import embed_texts
from app.services.llm import generate_response
from app.services.retrieval import retrieve
from app.services.tokenizer import count_tokens
from app.services.reranker import rerank


MAX_CONTEXT_TOKENS = 1500
MAX_PER_SOURCE = 2


def init_store(texts: list[str]):
    global vector_store

    vectors = embed_texts(texts)
    dim = len(vectors[0])

    vector_store = VectorStore(dim)
    vector_store.add(vectors, texts)


def ingest_document(text: str, source: str):
    chunks = chunk_text(text)

    vectors = embed_texts(chunks)

    metadata = [{"source": source, "chunk_id": i} for i in range(len(chunks))]

    vector_store.add(vectors, chunks, metadata)


def normalize(text: str) -> str:
    return " ".join(text.lower().strip().split())


def rag_query(question: str, session_id: str):
    docs = retrieve(question, limit=20)

    docs = rerank(question, docs, top_k=5)

    seen_keys = set()
    seen_texts = set()

    source_count = defaultdict(int)

    filtered_docs = []
    total_tokens = 0

    for doc in docs:
        source = doc["metadata"]["source"]
        chunk_id = doc["metadata"]["chunk_id"]
        text = doc["text"]

        key = (source, chunk_id)
        norm_text = normalize(text)

        if key in seen_keys:
            continue

        if norm_text in seen_texts:
            continue

        if source_count[source] >= MAX_PER_SOURCE:
            continue

        tokens = count_tokens(text)

        if total_tokens + tokens > MAX_CONTEXT_TOKENS:
            break

        seen_keys.add(key)
        seen_texts.add(norm_text)
        source_count[source] += 1

        filtered_docs.append(doc)
        total_tokens += tokens

    context = "\n\n".join(doc["text"] for doc in filtered_docs)

    prompt = f"""
You are a helpful AI assistant.

Answer ONLY using the provided context.

If unsure, say you don't know.

Context:
{context}

Question:
{question}
"""

    answer = generate_response(
        prompt,
        session_id=session_id,
    )

    sources = [
        {
            "source": doc["metadata"]["source"],
            "snippet": doc["text"][:200],
        }
        for doc in filtered_docs
    ]

    return {
        "answer": answer,
        "sources": sources,
    }
