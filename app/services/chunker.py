def chunk_words(
    text: str, chunk_words: int = 300, overlap_words: int = 50
) -> list[str]:
    words = text.split()
    chunks: list[str] = []
    stride = chunk_words - overlap_words
    if stride <= 0:
        raise ValueError("chunk_words must exceed overlap_words")

    for start in range(0, len(words), stride):
        span = words[start : start + chunk_words]
        if not span:
            break
        chunks.append(" ".join(span))

        if start + chunk_words >= len(words):
            break

    return chunks


def chunk_text(text: str, chunk_size: int = 300, overlap: int = 50) -> list[str]:
    return chunk_words(text, chunk_words=chunk_size, overlap_words=overlap)
