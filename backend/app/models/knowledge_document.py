import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
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


class KnowledgeDocument(Base):
    """One immutable revision of an organization document.

    Every content change creates a new revision. Only the newest revision of a
    slug is current; earlier revisions are kept for provenance so historical
    citations stay resolvable.
    """

    __tablename__ = "knowledge_documents"

    __table_args__ = (
        CheckConstraint(
            "verification_status IN ('draft', 'verified', 'retired')",
            name="knowledge_documents_verification_status_check",
        ),
        CheckConstraint(
            "revision > 0",
            name="knowledge_documents_revision_positive_check",
        ),
        CheckConstraint(
            "verification_status <> 'verified' "
            "OR (verified_by IS NOT NULL AND verified_at IS NOT NULL)",
            name="knowledge_documents_verified_provenance_check",
        ),
        UniqueConstraint(
            "slug",
            "revision",
            name="knowledge_documents_slug_revision_unique",
        ),
        Index(
            "uq_knowledge_documents_current_slug",
            "slug",
            unique=True,
            postgresql_where=text("is_current = true"),
        ),
        {"schema": "public"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    slug: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)

    # Monotonic revision assigned by ingestion.
    revision: Mapped[int] = mapped_column(Integer, nullable=False)

    # Version label declared by the document owner, e.g. "2.1".
    source_version: Mapped[str] = mapped_column(Text, nullable=False)

    owner: Mapped[str | None] = mapped_column(Text, nullable=True)
    effective_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    source_path: Mapped[str] = mapped_column(Text, nullable=False)
    content_sha256: Mapped[str] = mapped_column(Text, nullable=False)

    verification_status: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default="draft",
    )
    verified_by: Mapped[str | None] = mapped_column(Text, nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    is_current: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="true",
    )

    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    superseded_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
