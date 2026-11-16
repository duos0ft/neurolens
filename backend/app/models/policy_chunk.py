import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class PolicyChunk(Base):
    __tablename__ = "policy_chunks"

    __table_args__ = (
        CheckConstraint(
            "chunk_index >= 0",
            name="policy_chunks_index_check",
        ),
        CheckConstraint(
            "page_number IS NULL OR page_number >= 1",
            name="policy_chunks_page_number_check",
        ),
        CheckConstraint(
            "token_count > 0",
            name="policy_chunks_token_count_check",
        ),
        CheckConstraint(
            "length(trim(content)) > 0",
            name="policy_chunks_content_check",
        ),
        UniqueConstraint(
            "version_id",
            "chunk_index",
            name="policy_chunks_version_index_unique",
        ),
        Index(
            "policy_chunks_version_id_idx",
            "version_id",
        ),
        {"schema": "public"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "public.policy_versions.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    chunk_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    section_title: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    page_number: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    token_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    embedding: Mapped[list[float]] = mapped_column(
        Vector(1536),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
