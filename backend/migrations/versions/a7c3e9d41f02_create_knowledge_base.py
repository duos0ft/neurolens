"""create knowledge base for policy retrieval

Revision ID: a7c3e9d41f02
Revises: 93bfb2d1ae18
Create Date: 2026-11-11 12:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import ARRAY

from migrations.runtime_access import RuntimeAccess, configure_runtime_access

# revision identifiers, used by Alembic.
revision: str = "a7c3e9d41f02"
down_revision: Union[str, Sequence[str], None] = "93bfb2d1ae18"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "knowledge_documents",
        sa.Column(
            "id",
            sa.UUID(),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("slug", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("source_version", sa.Text(), nullable=False),
        sa.Column("owner", sa.Text(), nullable=True),
        sa.Column("effective_date", sa.Date(), nullable=True),
        sa.Column("source_path", sa.Text(), nullable=False),
        sa.Column("content_sha256", sa.Text(), nullable=False),
        sa.Column(
            "verification_status",
            sa.Text(),
            nullable=False,
            server_default="draft",
        ),
        sa.Column("verified_by", sa.Text(), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "is_current",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
        sa.Column(
            "ingested_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("superseded_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "verification_status IN ('draft', 'verified', 'retired')",
            name="knowledge_documents_verification_status_check",
        ),
        sa.CheckConstraint(
            "revision > 0",
            name="knowledge_documents_revision_positive_check",
        ),
        sa.CheckConstraint(
            "verification_status <> 'verified' "
            "OR (verified_by IS NOT NULL AND verified_at IS NOT NULL)",
            name="knowledge_documents_verified_provenance_check",
        ),
        sa.UniqueConstraint(
            "slug",
            "revision",
            name="knowledge_documents_slug_revision_unique",
        ),
        schema="public",
    )

    op.create_index(
        "uq_knowledge_documents_current_slug",
        "knowledge_documents",
        ["slug"],
        unique=True,
        schema="public",
        postgresql_where=sa.text("is_current = true"),
    )

    op.create_table(
        "knowledge_chunks",
        sa.Column(
            "id",
            sa.UUID(),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "document_id",
            sa.UUID(),
            sa.ForeignKey("public.knowledge_documents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("section", sa.Text(), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding", ARRAY(sa.Float()), nullable=False),
        sa.Column("embedding_model", sa.Text(), nullable=False),
        sa.Column("embedding_dimensions", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "chunk_index >= 0",
            name="knowledge_chunks_index_check",
        ),
        sa.CheckConstraint(
            "length(btrim(content)) > 0",
            name="knowledge_chunks_content_check",
        ),
        sa.CheckConstraint(
            "cardinality(embedding) = embedding_dimensions",
            name="knowledge_chunks_embedding_dimensions_check",
        ),
        sa.UniqueConstraint(
            "document_id",
            "chunk_index",
            name="knowledge_chunks_document_index_unique",
        ),
        schema="public",
    )

    op.create_index(
        "ix_public_knowledge_chunks_document_id",
        "knowledge_chunks",
        ["document_id"],
        schema="public",
    )

    op.create_index(
        "ix_public_knowledge_chunks_embedding_model",
        "knowledge_chunks",
        ["embedding_model"],
        schema="public",
    )

    # The application only reads the knowledge base. Documents are ingested
    # by an operator through the privileged migration connection.
    configure_runtime_access("knowledge_documents", RuntimeAccess.READ_ONLY)
    configure_runtime_access("knowledge_chunks", RuntimeAccess.READ_ONLY)

    # Policy answers must be explicitly enabled by an administrator.
    # Before this revision the flag had no effect, so switching it off
    # does not change existing behaviour.
    op.alter_column(
        "application_settings",
        "enable_policy_assistance",
        server_default=sa.false(),
        schema="public",
    )
    op.execute("UPDATE public.application_settings SET enable_policy_assistance = false")


def downgrade() -> None:
    op.alter_column(
        "application_settings",
        "enable_policy_assistance",
        server_default=sa.true(),
        schema="public",
    )

    op.drop_index(
        "ix_public_knowledge_chunks_embedding_model",
        table_name="knowledge_chunks",
        schema="public",
    )
    op.drop_index(
        "ix_public_knowledge_chunks_document_id",
        table_name="knowledge_chunks",
        schema="public",
    )
    op.drop_table("knowledge_chunks", schema="public")

    op.drop_index(
        "uq_knowledge_documents_current_slug",
        table_name="knowledge_documents",
        schema="public",
    )
    op.drop_table("knowledge_documents", schema="public")
