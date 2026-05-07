"""Offline evaluation metrics (no I/O)."""

from evaluation.metrics import answer_semantic_ok, source_hit


def test_source_hit_overlap() -> None:
    assert source_hit(["a.pdf", "b.pdf"], [{"source": "a.pdf", "snippet": "x"}]) is True

    assert source_hit(["c.pdf"], [{"source": "other", "snippet": "y"}]) is False


def test_answer_semantic_ok_substring() -> None:
    assert answer_semantic_ok("Hello World", "prefix Hello World suffix") is True

    assert answer_semantic_ok("", "anything") is True


def test_answer_semantic_ok_word_fallback() -> None:
    """Overlap on >5-char tokens when the full phrase is not contiguous."""

    assert answer_semantic_ok(
        "alpha bravo charlie delta echo",
        "alpha bravo charlie delta echo and more detail",
    ) is True
