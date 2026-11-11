import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class KnowledgeChunk(Base):
    """A retrievable passage of a knowledge document revision.

    Embeddings are stored as a plain float array so the schema runs on any
    PostgreSQL instance. ``embedding_model`` records the vector space; the
    retriever only compares vectors produced by the same model.
    """

    __tablename__ = "knowledge_chunks"

    __table_args__ = (
        CheckConstraint(
            "chunk_index >= 0",
            name="knowledge_chunks_index_check",
        ),
        CheckConstraint(
            "length(btrim(content)) > 0",
            name="knowledge_chunks_content_check",
        ),
        CheckConstraint(
            "cardinality(embedding) = embedding_dimensions",
            name="knowledge_chunks_embedding_dimensions_check",
        ),
        UniqueConstraint(
            "document_id",
            "chunk_index",
            name="knowledge_chunks_document_index_unique",
        ),
        {"schema": "public"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("public.knowledge_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    section: Mapped[str | None] = mapped_column(Text, nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    embedding: Mapped[list[float]] = mapped_column(ARRAY(Float), nullable=False)
    embedding_model: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    embedding_dimensions: Mapped[int] = mapped_column(Integer, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
