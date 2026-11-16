"""add calendar sync operations

Revision ID: f3f27281bdc5
Revises: bab80a913938
Create Date: 2026-11-14 11:18:31.461675

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f3f27281bdc5"
down_revision: Union[str, Sequence[str], None] = "bab80a913938"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "calendar_sync_records",
        sa.Column(
            "operation",
            sa.Text(),
            nullable=False,
            server_default="upsert",
        ),
        schema="public",
    )

    op.add_column(
        "calendar_sync_records",
        sa.Column(
            "revision",
            sa.Integer(),
            nullable=False,
            server_default="1",
        ),
        schema="public",
    )

    op.add_column(
        "calendar_sync_records",
        sa.Column(
            "attempt_id",
            sa.UUID(),
            nullable=True,
        ),
        schema="public",
    )

    op.add_column(
        "calendar_sync_records",
        sa.Column(
            "lease_expires_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        schema="public",
    )

    op.create_check_constraint(
        "calendar_sync_records_operation_check",
        "calendar_sync_records",
        "operation IN ('upsert', 'delete')",
        schema="public",
    )

    op.create_check_constraint(
        "calendar_sync_records_revision_check",
        "calendar_sync_records",
        "revision >= 1",
        schema="public",
    )

    op.create_index(
        "calendar_sync_records_lease_idx",
        "calendar_sync_records",
        ["status", "lease_expires_at"],
        schema="public",
    )


def downgrade() -> None:
    op.drop_index(
        "calendar_sync_records_lease_idx",
        table_name="calendar_sync_records",
        schema="public",
    )

    op.drop_constraint(
        "calendar_sync_records_revision_check",
        "calendar_sync_records",
        type_="check",
        schema="public",
    )

    op.drop_constraint(
        "calendar_sync_records_operation_check",
        "calendar_sync_records",
        type_="check",
        schema="public",
    )

    for column in (
        "lease_expires_at",
        "attempt_id",
        "revision",
        "operation",
    ):
        op.drop_column(
            "calendar_sync_records",
            column,
            schema="public",
        )
