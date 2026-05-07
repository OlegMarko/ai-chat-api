from sqlalchemy import Column, Integer, String, Text, UniqueConstraint

from pgvector.sqlalchemy import Vector

from app.core.config import settings
from app.db.database import Base


class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    __table_args__ = (
        UniqueConstraint("source", "chunk_id", name="uq_document_chunks_source_chunk"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)

    source = Column(String(2048), nullable=False)
    chunk_id = Column(Integer, nullable=False)

    content = Column(Text, nullable=False)

    embedding = Column(Vector(settings.embedding_dimensions))
