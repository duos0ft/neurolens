"""add policy knowledge base

Revision ID: 66617f85650d
Revises: f3f27281bdc5
Create Date: 2026-11-15 17:10:18.565753

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

from migrations.runtime_access import RuntimeAccess, configure_runtime_access

# revision identifiers, used by Alembic.
revision: str = "66617f85650d"
down_revision: Union[str, Sequence[str], None] = "f3f27281bdc5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("SET LOCAL search_path TO public, extensions")
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "policy_documents",
        sa.Column(
            "id",
            sa.UUID(),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "title",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "description",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "category",
            sa.Text(),
            nullable=False,
            server_default="other",
        ),
        sa.Column(
            "created_by",
            sa.UUID(),
            sa.ForeignKey(
                "public.employees.user_id",
                ondelete="SET NULL",
            ),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "category IN ("
            "'leave', "
            "'remote_work', "
            "'working_hours', "
            "'communication', "
            "'accessibility', "
            "'information_security', "
            "'other'"
            ")",
            name="policy_documents_category_check",
        ),
        schema="public",
    )

    op.create_index(
        "policy_documents_category_idx",
        "policy_documents",
        ["category"],
        schema="public",
    )

    op.create_table(
        "policy_versions",
        sa.Column(
            "id",
            sa.UUID(),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "document_id",
            sa.UUID(),
            sa.ForeignKey(
                "public.policy_documents.id",
                ondelete="CASCADE",
            ),
            nullable=False,
        ),
        sa.Column(
            "version_number",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "file_path",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "original_filename",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "content_type",
            sa.Text(),
            nullable=False,
            server_default="application/pdf",
        ),
        sa.Column(
            "file_size_bytes",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "effective_date",
            sa.Date(),
            nullable=True,
        ),
        sa.Column(
            "ingestion_status",
            sa.Text(),
            nullable=False,
            server_default="pending",
        ),
        sa.Column(
            "publication_status",
            sa.Text(),
            nullable=False,
            server_default="draft",
        ),
        sa.Column(
            "ingestion_error_code",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "uploaded_by",
            sa.UUID(),
            sa.ForeignKey(
                "public.employees.user_id",
                ondelete="SET NULL",
            ),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "published_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "archived_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.CheckConstraint(
            "version_number >= 1",
            name="policy_versions_version_number_check",
        ),
        sa.CheckConstraint(
            "file_size_bytes > 0",
            name="policy_versions_file_size_check",
        ),
        sa.CheckConstraint(
            "ingestion_status IN ('pending', 'processing', 'ready', 'failed')",
            name="policy_versions_ingestion_status_check",
        ),
        sa.CheckConstraint(
            "publication_status IN ('draft', 'published', 'archived')",
            name="policy_versions_publication_status_check",
        ),
        sa.CheckConstraint(
            "publication_status != 'published' OR ingestion_status = 'ready'",
            name="policy_versions_published_ready_check",
        ),
        sa.CheckConstraint(
            "publication_status != 'published' OR published_at IS NOT NULL",
            name="policy_versions_published_at_check",
        ),
        sa.UniqueConstraint(
            "document_id",
            "version_number",
            name="policy_versions_document_version_unique",
        ),
        schema="public",
    )

    op.create_index(
        "ix_policy_versions_document_id",
        "policy_versions",
        ["document_id"],
        schema="public",
    )

    op.create_index(
        "policy_versions_one_published_per_document_idx",
        "policy_versions",
        ["document_id"],
        unique=True,
        postgresql_where=sa.text("publication_status = 'published'"),
        schema="public",
    )

    op.create_table(
        "policy_chunks",
        sa.Column(
            "id",
            sa.UUID(),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "version_id",
            sa.UUID(),
            sa.ForeignKey(
                "public.policy_versions.id",
                ondelete="CASCADE",
            ),
            nullable=False,
        ),
        sa.Column(
            "chunk_index",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "content",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "section_title",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "page_number",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "token_count",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "embedding",
            Vector(1536),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "chunk_index >= 0",
            name="policy_chunks_index_check",
        ),
        sa.CheckConstraint(
            "page_number IS NULL OR page_number >= 1",
            name="policy_chunks_page_number_check",
        ),
        sa.CheckConstraint(
            "token_count > 0",
            name="policy_chunks_token_count_check",
        ),
        sa.CheckConstraint(
            "length(trim(content)) > 0",
            name="policy_chunks_content_check",
        ),
        sa.UniqueConstraint(
            "version_id",
            "chunk_index",
            name="policy_chunks_version_index_unique",
        ),
        schema="public",
    )

    op.create_index(
        "policy_chunks_version_id_idx",
        "policy_chunks",
        ["version_id"],
        schema="public",
    )

    op.execute(
        """
        CREATE TRIGGER policy_documents_updated_at
            BEFORE UPDATE ON public.policy_documents
            FOR EACH ROW
            EXECUTE FUNCTION public.set_updated_at()
        """
    )

    op.execute(
        """
        CREATE TRIGGER policy_versions_updated_at
            BEFORE UPDATE ON public.policy_versions
            FOR EACH ROW
            EXECUTE FUNCTION public.set_updated_at()
        """
    )

    configure_runtime_access(
        "policy_documents",
        RuntimeAccess.READ_WRITE,
    )

    configure_runtime_access(
        "policy_versions",
        RuntimeAccess.READ_WRITE,
    )

    configure_runtime_access(
        "policy_chunks",
        RuntimeAccess.READ_WRITE,
    )


def downgrade() -> None:
    op.execute(
        """
        DROP TRIGGER IF EXISTS policy_versions_updated_at
        ON public.policy_versions
        """
    )

    op.execute(
        """
        DROP TRIGGER IF EXISTS policy_documents_updated_at
        ON public.policy_documents
        """
    )

    op.drop_table(
        "policy_chunks",
        schema="public",
    )

    op.drop_table(
        "policy_versions",
        schema="public",
    )

    op.drop_table(
        "policy_documents",
        schema="public",
    )
