import json
import time

from evaluation.metrics import (
    source_hit,
    answer_contains,
)

from app.services.rag import rag_query


def run_evaluation():
    with open("evaluation/dataset.json") as f:
        dataset = json.load(f)

    results = []

    for item in dataset:
        start = time.time()

        response = rag_query(question=item["question"], session_id="eval")

        latency = time.time() - start

        retrieval_ok = source_hit(item["expected_sources"], response["sources"])

        answer_ok = answer_contains(item["expected_answer"], response["answer"])

        results.append(
            {
                "question": item["question"],
                "retrieval_ok": retrieval_ok,
                "answer_ok": answer_ok,
                "latency": latency,
            }
        )

    return results
