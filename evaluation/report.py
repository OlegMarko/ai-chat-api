"""CLI report for `python -m evaluation.report`."""

import json
from pathlib import Path


def main() -> None:
    from evaluation.evaluator import run_evaluation

    results = run_evaluation()

    n = len(results)

    if n == 0:
        print("No dataset rows.")
        return

    retrieval = sum(r["retrieval_ok"] for r in results) / n
    answers = sum(r["answer_ok"] for r in results) / n
    latency = sum(r["latency_seconds"] for r in results) / n

    print("\n=== Evaluation Report ===\n")
    print(f"Cases: {n}")
    print(f"Retrieval hit-rate: {retrieval:.2%}")
    print(f"Answer quality: {answers:.2%}")
    print(f"Mean latency (s): {latency:.2f}\n")

    for row in results:
        print(f"Q: {row['question']}")
        print(
            f"retrieval_ok={row['retrieval_ok']}"
            f"answer_ok={row['answer_ok']} "
            f"latency_s={row['latency_seconds']:.2f}",
        )
        print("-" * 40)

    out_dir = Path(__file__).resolve().parent / "reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "results.json"
    out_file.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\nWrote {out_file}")


if __name__ == "__main__":
    main()
