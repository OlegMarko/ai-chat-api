import logging

from fastapi import APIRouter, Request

from app.deps import OpenAIDepAnnotated, RedisDepAnnotated, SessionDepAnnotated
from app.schemas import IngestRequest, QueryRequest, RAGResponse
from app.security.ratelimit import gate_rag_burst
from app.services.ingest import ingest_document_async
from app.services.rag import rag_query

router = APIRouter(tags=["rag"])

logger = logging.getLogger(__name__)


def _client_ip(req: Request) -> str:
    if req.client is None:
        return "anon"

    return req.client.host


@router.post("/ingest")
async def ingest_documents(
    body: IngestRequest,
    request: Request,
    session: SessionDepAnnotated,
    openai_client: OpenAIDepAnnotated,
    redis: RedisDepAnnotated,
) -> dict[str, str | int]:
    await gate_rag_burst(redis, _client_ip(request))

    chunks = 0

    for doc in body.documents:
        chunks += await ingest_document_async(
            session,
            openai_client,
            source=doc.source,
            text=doc.text,
        )

    logger.info("ingest_done chunks=%s documents=%s", chunks, len(body.documents))

    return {
        "status": "ok",
        "chunk_count": chunks,
        "document_count": len(body.documents),
    }


@router.post("/rag", response_model=RAGResponse)
async def run_rag(
    body: QueryRequest,
    request: Request,
    session: SessionDepAnnotated,
    openai_client: OpenAIDepAnnotated,
    redis: RedisDepAnnotated,
) -> RAGResponse:
    await gate_rag_burst(redis, _client_ip(request))

    payload = await rag_query(
        session=session,
        openai_client=openai_client,
        redis=redis,
        question=body.question.strip(),
        session_id=body.session_id,
    )

    return RAGResponse.model_validate(payload)
