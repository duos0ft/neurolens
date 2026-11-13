"""add calendar oauth flows

Revision ID: 011c463abfca
Revises: 9245c9698448
Create Date: 2026-11-14 00:38:44.846367

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from migrations.runtime_access import configure_runtime_access, RuntimeAccess

# revision identifiers, used by Alembic.
revision: str = "011c463abfca"
down_revision: Union[str, Sequence[str], None] = "9245c9698448"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "calendar_oauth_flows",
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
            "state_hash",
            sa.Text(),
            nullable=False,
            unique=True,
        ),
        sa.Column(
            "browser_nonce_hash",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "session_hash",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "code_verifier",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "return_path",
            sa.Text(),
            nullable=False,
            server_default="/app/settings/integrations",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "expires_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "consumed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.CheckConstraint(
            "provider IN ('google', 'microsoft')",
            name="calendar_oauth_flows_provider_check",
        ),
        sa.CheckConstraint(
            "expires_at > created_at",
            name="calendar_oauth_flows_valid_expiry",
        ),
        schema="public",
    )

    op.create_index(
        "calendar_oauth_flows_expires_at_idx",
        "calendar_oauth_flows",
        ["expires_at"],
        schema="public",
    )

    configure_runtime_access(
        "calendar_oauth_flows",
        RuntimeAccess.LIFECYCLE,
    )


def downgrade() -> None:
    op.drop_index(
        "calendar_oauth_flows_expires_at_idx",
        table_name="calendar_oauth_flows",
        schema="public",
    )

    op.drop_table(
        "calendar_oauth_flows",
        schema="public",
    )
