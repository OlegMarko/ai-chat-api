import asyncio
import logging

from sentence_transformers import CrossEncoder

from app.core.config import settings

logger = logging.getLogger(__name__)

_model_singleton: CrossEncoder | None = None


def _get_model_blocking() -> CrossEncoder:
    global _model_singleton
    if _model_singleton is None:
        logger.warning("loading_cross_encoder model=%s", settings.cross_encoder_model)
        _model_singleton = CrossEncoder(settings.cross_encoder_model)
    return _model_singleton


def _rerank_blocking(question: str, docs: list[dict], *, top_k: int) -> list[dict]:
    model = _get_model_blocking()
    texts = tuple(doc["text"] for doc in docs)
    pairs = [(question, tex) for tex in texts]

    scores_raw = model.predict(pairs, batch_size=24)
    zipped = tuple(zip(docs, scores_raw, strict=True))
    zipped_sorted = tuple(sorted(zipped, key=lambda x: float(x[1]), reverse=True))
    truncated = zipped_sorted[:top_k]

    return [tpl[0] for tpl in truncated]


async def rerank(question: str, docs: list[dict], *, top_k: int) -> list[dict]:
    if not docs:
        return []

    loop = asyncio.get_running_loop()

    return await loop.run_in_executor(
        None,
        lambda q=question, d=list(docs), k=top_k: _rerank_blocking(q, d, top_k=k),
    )
