from pydantic import BaseModel


class IngestRequest(BaseModel):
    texts: list[str]


class QueryRequest(BaseModel):
    session_id: str
    question: str


class Source(BaseModel):
    source: str
    snippet: str


class RAGResponse(BaseModel):
    answer: str
    sources: list[Source]
