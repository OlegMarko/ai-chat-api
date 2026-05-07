"""Chunking boundaries (pure)."""

from app.services.chunker import chunk_text, chunk_words


def test_chunk_words_non_overlapping_tail() -> None:
    words = [str(i) for i in range(350)]

    text = " ".join(words)

    chunks = chunk_words(text, chunk_words=300, overlap_words=50)

    assert len(chunks) == 2

    assert chunks[0].split()[0] == "0"

    assert chunks[-1].split()[-1] == "349"


def test_chunk_words_small_input() -> None:
    assert chunk_words("one two three", chunk_words=10, overlap_words=2) == ["one two three"]


def test_chunk_text_alias_matches_chunk_words() -> None:
    text = "a b c d e f g h"

    assert chunk_text(text, chunk_size=4, overlap=1) == chunk_words(text, chunk_words=4, overlap_words=1)
