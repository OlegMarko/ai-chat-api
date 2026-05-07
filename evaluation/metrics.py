def source_hit(expected_sources, actual_sources):
    actual = {s["source"] for s in actual_sources}

    expected = set(expected_sources)

    return len(actual & expected) > 0


def answer_contains(expected_answer, actual_answer):
    return expected_answer.lower() in actual_answer.lower()
