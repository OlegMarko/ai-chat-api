from pydantic import BaseModel, Field


class IngestDocumentItem(BaseModel):
    source: str = Field(..., max_length=2048)
    text: str = Field(..., min_length=1)


class IngestRequest(BaseModel):
    documents: list[IngestDocumentItem] = Field(..., min_length=1)


class QueryRequest(BaseModel):
    session_id: str = Field(..., min_length=1, max_length=256)
    question: str = Field(..., min_length=1)


class Source(BaseModel):
    source: str
    snippet: str


class RAGResponse(BaseModel):
    answer: str
    sources: list[Source]
