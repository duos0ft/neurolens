"""add policy ingestion leases

Revision ID: 0ea915f8f900
Revises: 66617f85650d
Create Date: 2026-11-15 21:04:03.758137

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0ea915f8f900"
down_revision: Union[str, Sequence[str], None] = "66617f85650d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "policy_versions",
        sa.Column(
            "processing_attempt_id",
            sa.UUID(),
            nullable=True,
        ),
        schema="public",
    )

    op.add_column(
        "policy_versions",
        sa.Column(
            "processing_lease_expires_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        schema="public",
    )

    op.add_column(
        "policy_versions",
        sa.Column(
            "ingestion_attempt_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        schema="public",
    )

    op.add_column(
        "policy_versions",
        sa.Column(
            "next_ingestion_retry_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        schema="public",
    )

    op.create_check_constraint(
        "policy_versions_ingestion_attempt_count_check",
        "policy_versions",
        "ingestion_attempt_count >= 0",
        schema="public",
    )

    op.create_check_constraint(
        "policy_versions_processing_lease_check",
        "policy_versions",
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
        schema="public",
    )

    op.create_index(
        "policy_versions_ingestion_queue_idx",
        "policy_versions",
        [
            "ingestion_status",
            "next_ingestion_retry_at",
            "processing_lease_expires_at",
        ],
        schema="public",
    )


def downgrade() -> None:
    op.drop_index(
        "policy_versions_ingestion_queue_idx",
        table_name="policy_versions",
        schema="public",
    )

    op.drop_constraint(
        "policy_versions_processing_lease_check",
        "policy_versions",
        type_="check",
        schema="public",
    )

    op.drop_constraint(
        "policy_versions_ingestion_attempt_count_check",
        "policy_versions",
        type_="check",
        schema="public",
    )

    for column in (
        "next_ingestion_retry_at",
        "ingestion_attempt_count",
        "processing_lease_expires_at",
        "processing_attempt_id",
    ):
        op.drop_column(
            "policy_versions",
            column,
            schema="public",
        )
