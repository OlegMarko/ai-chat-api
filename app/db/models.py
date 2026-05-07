from sqlalchemy import Column, Integer, String, Text
from pgvector.sqlalchemy import Vector

from app.db.database import Base


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True)

    source = Column(String, nullable=False)
    chunk_id = Column(Integer, nullable=False)

    content = Column(Text, nullable=False)

    embedding = Column(Vector(1536))
