from fastapi import APIRouter
from app.schemas import IngestRequest, QueryRequest, RAGResponse
from app.services.rag import init_store, rag_query

router = APIRouter()


@router.post("/ingest")
def ingest(req: IngestRequest):
    init_store(req.texts)
    return {"status": "ok"}


@router.post("/rag", response_model=RAGResponse)
def query(req: QueryRequest):
    result = rag_query(req.question, req.session_id)
    return result
