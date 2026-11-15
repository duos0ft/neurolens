"""add organization default timezone

Revision ID: 7ba688e89423
Revises: e372397f807b
Create Date: 2026-11-12 21:52:59.810672

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "7ba688e89423"
down_revision: Union[str, Sequence[str], None] = "e372397f807b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "application_settings",
        sa.Column(
            "default_timezone",
            sa.Text(),
            nullable=False,
            server_default="UTC",
        ),
        schema="public",
    )

    op.alter_column(
        "employee_profiles",
        "timezone",
        existing_type=sa.Text(),
        nullable=True,
        server_default=None,
        schema="public",
    )


def downgrade() -> None:
    # Existing NULL overrides must be converted before restoring
    # the original NOT NULL constraint.
    op.execute(
        """
        UPDATE public.employee_profiles
        SET timezone = 'UTC'
        WHERE timezone IS NULL
        """
    )

    op.alter_column(
        "employee_profiles",
        "timezone",
        existing_type=sa.Text(),
        nullable=False,
        server_default="UTC",
        schema="public",
    )

    op.drop_column(
        "application_settings",
        "default_timezone",
        schema="public",
    )
