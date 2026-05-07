"""Token-bounded history trimming."""

from app.services.history_builder import build_token_aware_history


def test_build_token_aware_history_prefers_newest_within_budget() -> None:
    messages = [
        {"role": "user", "content": "old"},
        {"role": "assistant", "content": "mid"},
        {"role": "user", "content": "newest"},
    ]

    # Large budget -> keep order (oldest..newest) after trim logic (reversed walk)
    out = build_token_aware_history(messages, max_prompt_tokens_budget=100_000)

    assert [m["content"] for m in out] == ["old", "mid", "newest"]


def test_build_token_aware_history_drops_oldest_when_tight_budget() -> None:
    """Newest turn kept first; older long message excluded when budget is tight."""

    long_old = "x" * 12_000
    short_new = "ping"

    messages = [
        {"role": "user", "content": long_old},
        {"role": "user", "content": short_new},
    ]

    # Margin inside build_token_aware_history leaves a finite slice; small budget keeps only newest.
    out = build_token_aware_history(messages, max_prompt_tokens_budget=256)

    assert len(out) == 1
    assert out[0]["content"] == short_new
