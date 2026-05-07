from __future__ import annotations

from collections import defaultdict
from typing import Any

from openai import AsyncOpenAI
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.services.llm import generate_response
from app.services.reranker import rerank
from app.services.retrieval import retrieve
from app.services.tokenizer import count_tokens


def _normalize(text: str) -> str:
    return " ".join(text.lower().strip().split())


def _pack_documents(
    docs: list[dict[str, Any]],
    *,
    max_chunks: int,
    max_tokens: int,
    max_per_source: int,
) -> list[dict[str, Any]]:
    seen_keys: set[tuple[str, int]] = set()
    seen_texts: set[str] = set()
    per_source = defaultdict(int)
    out: list[dict[str, Any]] = []
    total = 0

    for doc in docs:
        meta = doc["metadata"]
        source = meta["source"]
        chunk_id = int(meta["chunk_id"])
        body = str(doc["text"])

        key = (str(source), chunk_id)
        norm = _normalize(body)

        if key in seen_keys:
            continue
        seen_keys.add(key)

        if norm in seen_texts:
            continue
        seen_texts.add(norm)

        if per_source[str(source)] >= max_per_source:
            continue

        t = count_tokens(body)
        if total + t > max_tokens:
            break
        if len(out) >= max_chunks:
            break

        out.append(doc)
        total += t
        per_source[str(source)] += 1

    return out


async def rag_query(
    *,
    session: AsyncSession,
    openai_client: AsyncOpenAI,
    redis: Redis,
    question: str,
    session_id: str,
) -> dict[str, Any]:
    pool = await retrieve(
        session, embedding_client=openai_client, question=question.strip(), limit=None
    )

    k = min(settings.retrieval_rerank_top_k, len(pool)) if pool else 0
    reranked = await rerank(question, pool, top_k=k) if k else []

    packed = _pack_documents(
        reranked,
        max_chunks=settings.rag_context_max_chunks,
        max_tokens=settings.rag_context_max_tokens,
        max_per_source=settings.rag_max_per_source,
    )

    context = "\n\n".join(str(d["text"]) for d in packed)

    user_message = (
        "You answer strictly from the excerpts below. If they are insufficient, say you do not know.\n\n"
        f"Excerpts:\n{context}\n\n"
        f"Question:\n{question.strip()}"
    )

    answer = await generate_response(
        redis=redis,
        client=openai_client,
        session_id=session_id,
        message=user_message,
        rag_mode=True,
    )

    sources = [
        {
            "source": str(d["metadata"]["source"]),
            "snippet": str(d["text"])[:240],
        }
        for d in packed
    ]

    return {"answer": answer, "sources": sources}
