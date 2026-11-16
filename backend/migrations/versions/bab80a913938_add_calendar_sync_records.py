"""add calendar sync records

Revision ID: bab80a913938
Revises: 011c463abfca
Create Date: 2026-11-14 11:14:40.056198

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from migrations.runtime_access import RuntimeAccess, configure_runtime_access

# revision identifiers, used by Alembic.
revision: str = "bab80a913938"
down_revision: Union[str, Sequence[str], None] = "011c463abfca"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "calendar_sync_records",
        sa.Column(
            "id",
            sa.UUID(),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "integration_id",
            sa.UUID(),
            sa.ForeignKey(
                "public.calendar_integrations.id",
                ondelete="CASCADE",
            ),
            nullable=False,
        ),
        sa.Column(
            "source_type",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "source_id",
            sa.UUID(),
            nullable=False,
        ),
        sa.Column(
            "external_calendar_id",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "external_event_id",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "status",
            sa.Text(),
            nullable=False,
            server_default="pending",
        ),
        sa.Column(
            "retry_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "next_retry_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "last_synced_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "last_error_code",
            sa.Text(),
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
            "source_type IN ('task', 'calendar_event')",
            name="calendar_sync_records_source_type_check",
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'syncing', 'synced', 'failed')",
            name="calendar_sync_records_status_check",
        ),
        sa.CheckConstraint(
            "retry_count >= 0",
            name="calendar_sync_records_retry_count_check",
        ),
        sa.UniqueConstraint(
            "integration_id",
            "source_type",
            "source_id",
            name="calendar_sync_records_source_unique",
        ),
        schema="public",
    )

    op.create_index(
        "ix_calendar_sync_records_integration_id",
        "calendar_sync_records",
        ["integration_id"],
        schema="public",
    )

    op.create_index(
        "calendar_sync_records_pending_idx",
        "calendar_sync_records",
        ["status", "next_retry_at"],
        schema="public",
    )

    op.execute(
        """
        CREATE TRIGGER calendar_sync_records_updated_at
            BEFORE UPDATE ON public.calendar_sync_records
            FOR EACH ROW
            EXECUTE FUNCTION public.set_updated_at();
        """
    )

    configure_runtime_access(
        "calendar_sync_records",
        RuntimeAccess.LIFECYCLE,
    )


def downgrade() -> None:
    op.execute(
        """
        DROP TRIGGER IF EXISTS calendar_sync_records_updated_at
        ON public.calendar_sync_records
        """
    )

    op.drop_index(
        "calendar_sync_records_pending_idx",
        table_name="calendar_sync_records",
        schema="public",
    )

    op.drop_index(
        "ix_calendar_sync_records_integration_id",
        table_name="calendar_sync_records",
        schema="public",
    )

    op.drop_table(
        "calendar_sync_records",
        schema="public",
    )
