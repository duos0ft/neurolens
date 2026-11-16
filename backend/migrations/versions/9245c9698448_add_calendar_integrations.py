"""add calendar integrations

Revision ID: 9245c9698448
Revises: 47e6fa4eba9a
Create Date: 2026-11-14 00:29:38.151697

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from migrations.runtime_access import RuntimeAccess, configure_runtime_access

# revision identifiers, used by Alembic.
revision: str = "9245c9698448"
down_revision: Union[str, Sequence[str], None] = "47e6fa4eba9a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "calendar_integrations",
        sa.Column(
            "id",
            sa.UUID(),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "employee_id",
            sa.UUID(),
            sa.ForeignKey(
                "public.employees.user_id",
                ondelete="CASCADE",
            ),
            nullable=False,
        ),
        sa.Column(
            "provider",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "provider_account_id",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "account_email",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "encrypted_refresh_token",
            sa.LargeBinary(),
            nullable=False,
        ),
        sa.Column(
            "scopes",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "connected_at",
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
            "provider IN ('google', 'microsoft')",
            name="calendar_integrations_provider_check",
        ),
        sa.UniqueConstraint(
            "employee_id",
            "provider",
            name="calendar_integrations_employee_provider_unique",
        ),
        schema="public",
    )

    op.create_index(
        "ix_calendar_integrations_employee_id",
        "calendar_integrations",
        ["employee_id"],
        schema="public",
    )

    op.execute(
        """
        CREATE TRIGGER calendar_integrations_updated_at
            BEFORE UPDATE ON public.calendar_integrations
            FOR EACH ROW
            EXECUTE FUNCTION public.set_updated_at();
        """
    )

    configure_runtime_access(
        "calendar_integrations",
        RuntimeAccess.READ_WRITE,
    )


def downgrade() -> None:
    op.execute(
        """
        DROP TRIGGER IF EXISTS calendar_integrations_updated_at
        ON public.calendar_integrations
        """
    )

    op.drop_index(
        "ix_calendar_integrations_employee_id",
        table_name="calendar_integrations",
        schema="public",
    )

    op.drop_table(
        "calendar_integrations",
        schema="public",
    )
