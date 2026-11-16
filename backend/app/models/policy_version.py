import uuid
from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
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


class PolicyVersion(Base):
    __tablename__ = "policy_versions"

    __table_args__ = (
        CheckConstraint(
            "version_number >= 1",
            name="policy_versions_version_number_check",
        ),
        CheckConstraint(
            "ingestion_status IN ('pending', 'processing', 'ready', 'failed')",
            name="policy_versions_ingestion_status_check",
        ),
        CheckConstraint(
            "publication_status IN ('draft', 'published', 'archived')",
            name="policy_versions_publication_status_check",
        ),
        CheckConstraint(
            "publication_status != 'published' OR ingestion_status = 'ready'",
            name="policy_versions_published_ready_check",
        ),
        CheckConstraint(
            "publication_status != 'published' OR published_at IS NOT NULL",
            name="policy_versions_published_at_check",
        ),
        CheckConstraint(
            "ingestion_attempt_count >= 0",
            name="policy_versions_ingestion_attempt_count_check",
        ),
        CheckConstraint(
            """
            (
                ingestion_status = 'processing'
                AND processing_attempt_id IS NOT NULL
                AND processing_lease_expires_at IS NOT NULL
            )
            OR
            (
                ingestion_status != 'processing'
                AND processing_attempt_id IS NULL
                AND processing_lease_expires_at IS NULL
            )
            """,
            name="policy_versions_processing_lease_check",
        ),
        Index(
            "policy_versions_ingestion_queue_idx",
            "ingestion_status",
            "next_ingestion_retry_at",
            "processing_lease_expires_at",
        ),
        UniqueConstraint(
            "document_id",
            "version_number",
            name="policy_versions_document_version_unique",
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
        ForeignKey(
            "public.policy_documents.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    version_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    file_path: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    original_filename: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    content_type: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default="application/pdf",
    )

    file_size_bytes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    effective_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    ingestion_status: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default="pending",
    )

    publication_status: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default="draft",
    )

    ingestion_error_code: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    uploaded_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "public.employees.user_id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    archived_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    processing_attempt_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )

    processing_lease_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    ingestion_attempt_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default="0",
    )

    next_ingestion_retry_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
