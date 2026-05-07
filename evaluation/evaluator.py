"""Offline evaluation harness (async, isolated session + Redis namespace)."""

from __future__ import annotations

import asyncio
import json
import time
from pathlib import Path

from redis.asyncio import Redis

from app.db.database import AsyncSessionLocal
from app.infrastructure.openai_clients import create_shared_llm_client
from app.infrastructure.redis_pool import create_connection_pool, disconnect_pool
from app.services.history import clear_history
from app.services.rag import rag_query

from evaluation.metrics import answer_semantic_ok, source_hit


async def _evaluate_async() -> list[dict]:
    dataset_path = Path(__file__).resolve().parent / "dataset.json"
    dataset_payload = json.loads(dataset_path.read_text(encoding="utf-8"))

    redis_pool = create_connection_pool()

    redis_client = Redis(connection_pool=redis_pool)

    openai_client = create_shared_llm_client()

    await clear_history(redis_client, "eval")

    aggregated: list[dict] = []

    try:
        for probe in dataset_payload:
            t0 = time.perf_counter()

            async with AsyncSessionLocal() as session:
                response = await rag_query(
                    session=session,
                    openai_client=openai_client,
                    redis=redis_client,
                    question=str(probe["question"]),
                    session_id="eval",
                )

                await session.commit()

            latency = time.perf_counter() - t0

            retrieval_ok = source_hit(
                list(probe["expected_sources"]), response["sources"]
            )

            answer_ok_flag = answer_semantic_ok(
                str(probe["expected_answer"]), str(response["answer"])
            )

            aggregated.append(
                {
                    "question": probe["question"],
                    "retrieval_ok": retrieval_ok,
                    "answer_ok": answer_ok_flag,
                    "latency_seconds": latency,
                },
            )

        return aggregated

    finally:
        await disconnect_pool(redis_pool)


def run_evaluation() -> list[dict]:
    return asyncio.run(_evaluate_async())
