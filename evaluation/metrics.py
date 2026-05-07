"""Lightweight offline metrics (replace with nDCG / LLM-judge in CI)."""


def source_hit(expected_sources: list[str], actual_sources: list[dict]) -> bool:
    expected = {s.strip() for s in expected_sources}
    actual = {str(row["source"]).strip() for row in actual_sources}
    return bool(expected & actual)


def answer_semantic_ok(expected: str, actual: str) -> bool:
    exp = expected.strip().lower()
    act = actual.strip().lower()

    if not exp:
        return True

    if exp in act:
        return True

    words = [w for w in exp.split() if len(w) > 5]
    if not words:
        return False

    hits = sum(1 for w in words if w in act)
    return hits / len(words) >= 0.6
