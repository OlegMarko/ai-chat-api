import json
from evaluation.evaluator import run_evaluation


# python -m evaluation.report
if __name__ == "__main__":
    results = run_evaluation()

    total = len(results)

    retrieval_score = sum(r["retrieval_ok"] for r in results) / total

    answer_score = sum(r["answer_ok"] for r in results) / total

    avg_latency = sum(r["latency"] for r in results) / total

    print("\n=== Evaluation Report ===\n")

    print(f"Total tests: {total}")
    print(f"Retrieval accuracy: {retrieval_score:.2%}")
    print(f"Answer accuracy: {answer_score:.2%}")
    print(f"Average latency: {avg_latency:.2f}s")

    print("\n=== Detailed Results ===\n")

    for r in results:
        print(f"Question: {r['question']}")
        print(f"Retrieval OK: {r['retrieval_ok']}")
        print(f"Answer OK: {r['answer_ok']}")
        print(f"Latency: {r['latency']:.2f}s")
        print("-" * 40)

    with open("reports/results.json", "w") as f:
        json.dump(results, f, indent=2)
